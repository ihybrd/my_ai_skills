---
name: gdc-url-to-vtt
description: When the user provides a GDC Vault video page URL (not a VTT URL), automatically extract a VTT caption URL and then process it using the gdc-vtt-to-note workflow.
---

# GDC URL to VTT Skill (Parent)

## Purpose
This is the **parent skill** for `gdc-vtt-to-note`. It handles the case where the user provides a GDC Vault **video page URL** rather than a raw VTT segment URL.

It automatically:
1. Authenticates with GDC Vault
2. Parses the video page to extract the Blazestreaming video ID
3. Follows the CDN chain to locate a VTT caption segment URL
4. Delegates to the `gdc-vtt-to-note` workflow to capture, summarize, and create an Obsidian note

## Trigger
- User provides a **GDC Vault video page URL**, e.g.:
  - `https://gdcvault.com/play/1035765/Artists-Do-You-Want-to`
  - Any URL matching `gdcvault.com/play/*`
- Do NOT trigger when the user provides a raw `.vtt` URL — that is handled by `gdc-vtt-to-note` directly.

## Required Input
- A GDC Vault video page URL (the page you watch the video on, NOT a VTT file URL)
- GDC Vault credentials (email + password)

## Credential Resolution
Credentials are needed for Step 1. Look for them in this order:
1. Read the note `literature notes/video notes/gdc/GDC password.md` for the latest username/password
2. If not found, ask the user to provide `--email` and `--password`

## Workflow

### Step 1: Extract VTT URL
Run the bundled extraction script with the user's video URL and credentials:

```bash
python3 .claude/skills/gdc-url-to-vtt/scripts/extract_vtt_url.py \
  "<gdc_video_url>" \
  --email "<email>" \
  --password "<password>"
```

The script:
- Logs into GDC Vault (cookies are saved to `.claude/skills/gdc-url-to-vtt/scripts/.gdc_cookies.txt` for reuse)
- Extracts the Blazestreaming `videoId` from the page
- Follows the HLS manifest chain to find the first VTT caption segment
- Prints the **full VTT URL** to stdout

**If extraction fails:**
- Report the error to the user
- Common failures: expired credentials, page not found, no subtitle track
- Do NOT proceed to Step 2

### Step 2: Capture Captions (delegate to gdc-vtt-to-note)
Once the VTT URL is obtained, run the capture script from `gdc-vtt-to-note`:

```bash
python3 .claude/skills/gdc-vtt-to-note/scripts/capture_gdc_vtt.py \
  "<vtt_url_from_step_1>" \
  --output captions.txt
```

This brute-forces all VTT chunk IDs to assemble the full caption stream.

If the script fails, report the error and do NOT proceed.

### Step 3: Summarize & Create Note (follow gdc-vtt-to-note post-processing)
Once `captions.txt` is generated:

1. Read the generated caption file
2. Build a concise summary including:
   - Topic
   - Key points
   - Actionable insights
3. Create an Obsidian note in `literature notes/video notes/gdc/ai notes`

### Note Naming Rule
- Filename format: `YYYY-MM-DD-{summary_slug}.md`
- Slug rules: lowercase, spaces → `-`, remove invalid filename characters
- If conflict exists, append `-2`, `-3`, etc.

### Note Content
Include:
- Title
- Source GDC video URL
- Resolved VTT URL
- Caption file path
- Summary sections
- Captions.txt full content as reference

Prefer frontmatter metadata:
- `source_url`: the original GDC video page URL
- `source_vtt`: the resolved VTT segment URL
- `caption_file`: path to captions.txt
- `created_at`: today's date
- `tags: [gdc, summary]`

## Safety
- If Step 1 (VTT extraction) fails, report the error and stop
- If Step 2 (caption capture) fails, report stderr and do not create the note
- If caption file is empty, create note with `incomplete` status
- Never modify the `gdc-vtt-to-note` skill or its scripts
- Cookie jar file is stored alongside the script — add to `.gitignore` if needed
