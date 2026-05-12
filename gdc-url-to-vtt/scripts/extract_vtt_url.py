"""
Usage:
  python3 extract_vtt_url.py <gdc_video_url> --email <email> --password <password>
  python3 extract_vtt_url.py <gdc_video_url> --cookie-jar <path>

Workflow:
  1. Login to GDC Vault (or reuse saved cookies)
  2. Fetch video page → extract blazestreaming iframe → get videoId
  3. Construct master m3u8 URL using known CDN template
  4. Fetch master m3u8 → find subtitle playlist URI
  5. Fetch subtitle m3u8 → resolve first VTT segment URL
  6. Print the VTT URL to stdout

Example:
  python3 extract_vtt_url.py \
    "https://gdcvault.com/play/1035765/Artists-Do-You-Want-to" \
    --email "ubisoft@gdcvault.com" \
    --password "UbSfT200VA424#"
"""

import argparse
import os
import re
import sys
import time
from http.cookiejar import MozillaCookieJar
from urllib.parse import urljoin, urlparse, parse_qs

import requests

# --- Constants ---
LOGIN_URL = "https://gdcvault.com/api/login.php"
BLAZESTREAMING_BASE = "https://gdcvault.blazestreaming.com"
SCRIPT_VOD_URL = "https://gdcvault.blazestreaming.com/script_VOD.js"
# These hashes are hardcoded in Blazestreaming's script_VOD.js and appear to be static
# across all GDC Vault videos.
CDN_BASE = "https://cdn-a.blazestreaming.com/out/v1"
CDN_HASH_1 = "38549d9a185b445888c6fbc2e2e792e9"
CDN_HASH_2 = "50413c5b8a95441e919f0a1579606e47"
DEFAULT_COOKIE_JAR = os.path.join(os.path.dirname(__file__), ".gdc_cookies.txt")
REQUEST_TIMEOUT = 15

# --- Cookie persistence ---
def load_cookies(session: requests.Session, cookie_jar_path: str) -> bool:
    """Load cookies from a Mozilla-format cookie jar file. Returns True if loaded."""
    if not os.path.exists(cookie_jar_path):
        return False
    try:
        jar = MozillaCookieJar(cookie_jar_path)
        jar.load(ignore_discard=True, ignore_expires=True)
        session.cookies.update(jar)
        return len(jar) > 0
    except Exception:
        return False


def save_cookies(session: requests.Session, cookie_jar_path: str) -> None:
    """Save session cookies to a Mozilla-format cookie jar file."""
    jar = MozillaCookieJar(cookie_jar_path)
    for cookie in session.cookies:
        jar.set_cookie(cookie)
    jar.save(ignore_discard=True, ignore_expires=True)


# --- Step 1: Login ---
def login(session: requests.Session, email: str, password: str) -> bool:
    """Login to GDC Vault. Returns True on success."""
    try:
        resp = session.post(
            LOGIN_URL,
            data={"email": email, "password": password, "remember_me": "1"},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            print(f"Login failed: HTTP {resp.status_code}", file=sys.stderr)
            return False

        data = resp.json()
        if data.get("email") == email and data.get("isSubscribed") is True:
            print(f"Login successful: {data.get('fullname', email)}", file=sys.stderr)
            return True
        else:
            print(f"Login failed: unexpected response", file=sys.stderr)
            return False
    except requests.RequestException as exc:
        print(f"Login request failed: {exc}", file=sys.stderr)
        return False
    except ValueError:
        print(f"Login failed: non-JSON response (likely wrong credentials)", file=sys.stderr)
        return False


# --- Step 2: Extract videoId from video page ---
def extract_video_id(session: requests.Session, video_url: str) -> str | None:
    """Fetch the GDC video page and extract the Blazestreaming videoId."""
    try:
        resp = session.get(video_url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"Failed to fetch video page: {exc}", file=sys.stderr)
        return None

    html = resp.text

    # Check if redirected to login page
    if '<form id="form_login_page"' in html:
        print("Not authenticated — page redirected to login.", file=sys.stderr)
        return None

    # Find the blazestreaming iframe: src="https://gdcvault.blazestreaming.com/?id=XXX"
    pattern = r'https?://gdcvault\.blazestreaming\.com/\?id=([a-f0-9]+)'
    match = re.search(pattern, html)
    if match:
        video_id = match.group(1)
        print(f"Extracted videoId: {video_id}", file=sys.stderr)
        return video_id

    print("Could not find Blazestreaming iframe in page.", file=sys.stderr)
    return None


# --- Step 3: Build master m3u8 URL ---
def build_master_m3u8_url(video_id: str) -> str:
    """Construct the master HLS manifest URL using the known CDN template."""
    return f"{CDN_BASE}/{video_id}/{CDN_HASH_1}/{CDN_HASH_2}/index.m3u8"


# --- Step 4: Find subtitle playlist URI in master m3u8 ---
def find_subtitle_uri(master_m3u8_text: str) -> str | None:
    """Parse the master m3u8 and return the URI of the subtitle playlist."""
    # Look for: #EXT-X-MEDIA:TYPE=SUBTITLES,...,URI="..."
    pattern = r'#EXT-X-MEDIA:TYPE=SUBTITLES.*?URI="([^"]+)"'
    match = re.search(pattern, master_m3u8_text)
    if match:
        return match.group(1)
    return None


# --- Step 5: Resolve first VTT segment from subtitle playlist ---
def find_first_vtt_segment(subtitle_m3u8_text: str, subtitle_m3u8_url: str) -> str | None:
    """Parse the subtitle m3u8, find the first .vtt segment, and resolve its full URL."""
    for line in subtitle_m3u8_text.splitlines():
        line = line.strip()
        if line.endswith(".vtt") and not line.startswith("#"):
            full_url = urljoin(subtitle_m3u8_url, line)
            return full_url
    return None


# --- Main extraction flow ---
def extract_vtt_url(
    video_url: str,
    email: str | None = None,
    password: str | None = None,
    cookie_jar_path: str | None = None,
) -> str | None:
    """
    Full extraction pipeline. Returns the first VTT segment URL or None on failure.
    """
    session = requests.Session()
    session.headers.update(
        {"User-Agent": "Mozilla/5.0 (compatible; GDC-VTT-Extractor/1.0)"}
    )

    # Try to reuse saved cookies first
    logged_in = False
    if cookie_jar_path:
        if load_cookies(session, cookie_jar_path):
            print("Loaded saved cookies.", file=sys.stderr)
            # Test if cookies are still valid by fetching the video page
            try:
                test_resp = session.get(video_url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
                if '<form id="form_login_page"' not in test_resp.text:
                    logged_in = True
                    print("Saved cookies are still valid.", file=sys.stderr)
                else:
                    print("Saved cookies expired, re-logging in...", file=sys.stderr)
            except Exception:
                print("Cookie validation failed, re-logging in...", file=sys.stderr)

    # Login with credentials if needed
    if not logged_in and email and password:
        if not login(session, email, password):
            return None
        logged_in = True
        if cookie_jar_path:
            save_cookies(session, cookie_jar_path)
            print(f"Cookies saved to {cookie_jar_path}", file=sys.stderr)

    if not logged_in:
        print(
            "Not authenticated. Provide --email/--password or a valid --cookie-jar.",
            file=sys.stderr,
        )
        return None

    # Step 2: Extract videoId
    video_id = extract_video_id(session, video_url)
    if not video_id:
        return None

    # Step 3: Build master m3u8 URL
    master_url = build_master_m3u8_url(video_id)
    print(f"Master m3u8: {master_url}", file=sys.stderr)

    # Step 4: Fetch master m3u8 and find subtitle URI
    try:
        resp = session.get(master_url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"Failed to fetch master m3u8: {exc}", file=sys.stderr)
        return None

    subtitle_uri = find_subtitle_uri(resp.text)
    if not subtitle_uri:
        print("No subtitle track found in master m3u8.", file=sys.stderr)
        return None
    print(f"Subtitle URI: {subtitle_uri}", file=sys.stderr)

    # Step 5: Resolve subtitle m3u8 and extract first VTT segment
    subtitle_m3u8_url = urljoin(master_url, subtitle_uri)
    try:
        resp = session.get(subtitle_m3u8_url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"Failed to fetch subtitle m3u8: {exc}", file=sys.stderr)
        return None

    vtt_url = find_first_vtt_segment(resp.text, subtitle_m3u8_url)
    if not vtt_url:
        print("No VTT segments found in subtitle playlist.", file=sys.stderr)
        return None

    print(f"VTT segment URL: {vtt_url}", file=sys.stderr)
    return vtt_url


# --- CLI ---
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract a VTT segment URL from a GDC Vault video page."
    )
    parser.add_argument("url", help="GDC Vault video page URL")
    parser.add_argument("--email", help="GDC Vault login email")
    parser.add_argument("--password", help="GDC Vault login password")
    parser.add_argument(
        "--cookie-jar",
        default=DEFAULT_COOKIE_JAR,
        help=f"Path to cookie jar file (default: {DEFAULT_COOKIE_JAR})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Also check environment variables
    email = args.email or os.environ.get("GDC_EMAIL")
    password = args.password or os.environ.get("GDC_PASSWORD")

    start = time.time()
    vtt_url = extract_vtt_url(
        video_url=args.url,
        email=email,
        password=password,
        cookie_jar_path=args.cookie_jar,
    )

    elapsed = time.time() - start

    if vtt_url:
        # Output ONLY the URL to stdout (so it can be piped)
        print(vtt_url)
        print(f"Done in {elapsed:.1f}s", file=sys.stderr)
    else:
        print("Failed to extract VTT URL.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
