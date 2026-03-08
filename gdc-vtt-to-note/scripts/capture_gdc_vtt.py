"""
Usage:
  python3 capture_gdc_vtt.py "<vtt_segment_url>"

Workflow:
  1. Login to your GDC Vault account and open the target session page.
  2. Play the video, then open browser DevTools -> Network.
  3. Find any `.vtt` request and copy its URL.
  4. Run this script with that URL as the input parameter.

Example:
  python3 capture_gdc_vtt.py \
    "https://.../index_4_0_33.vtt" \
    --output captions.txt \
    --max-range 1000 \
    --max-404 3

How it works:
  - Any single `.vtt` URL is used as a sample to get the common caption path template.
  - The script brute-forces chunk ids in a while-loop (`..._%d.vtt`) to fetch the full stream.
  - If some chunk fails (e.g., timeout or missing file), it logs and skips that chunk.
  - After more than `--max-404` 404 responses, it assumes there are no more caption chunks and writes the merged output file.
"""

import argparse
import time
import traceback

import requests

DEFAULT_MAX_RANGE = 1000
DEFAULT_MAX_404_COUNT = 3
DEFAULT_OUTPUT = "captions.txt"
REQUEST_TIMEOUT_SECONDS = 10


def build_url_template(url: str) -> str:
    # ".../index_4_0_33.vtt" -> ".../index_4_0_%d.vtt"
    return "_".join(url.split("_", 3)[:3]) + "_%d.vtt"


def parse_chunk(raw_content: bytes) -> str:
    content = raw_content.decode("utf-8").replace("\\n\\n", "\n").strip() + "\n\n"
    lines = content.split("\n\n")

    parts = []
    for index, line in enumerate(lines):
        # index > 0: skip header
        # index != len(lines)-2: skip duplicated tail line
        # line: keep only non-empty blocks
        if index > 0 and line and index != len(lines) - 2:
            parts.append(line + "\n\n")
    return "".join(parts)


def capture_captions(template: str, max_chunk_index: int, max_404_count: int) -> str:
    chunks = []
    consecutive_404 = 0
    chunk_index = 0

    while True:
        if consecutive_404 > max_404_count:
            break
        if chunk_index > max_chunk_index:
            print(f"Reach max_chunk_index: {max_chunk_index}")
            break

        try:
            response = requests.get(template % chunk_index, timeout=REQUEST_TIMEOUT_SECONDS)
        except requests.RequestException as exc:
            tb = traceback.extract_tb(exc.__traceback__)
            if tb:
                last = tb[-1]
                print(
                    "Request failed at chunk {0}: {1}\n"
                    "Location: function={2}, file={3}, line={4}".format(
                        chunk_index, exc, last.name, last.filename, last.lineno
                    )
                )
            else:
                print(f"Request failed at chunk {chunk_index}: {exc}")
            chunk_index += 1
            continue

        if response.status_code == 404:
            print("status code: 404")
            consecutive_404 += 1

        chunks.append(parse_chunk(response.content))
        print(f"chunk {chunk_index}")
        chunk_index += 1

    return "".join(chunks)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture and merge segmented VTT captions.")
    parser.add_argument("url", help="One VTT segment URL, e.g. .../index_4_0_33.vtt")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output file path")
    parser.add_argument("--max-range", type=int, default=DEFAULT_MAX_RANGE, help="Max chunk index to try")
    parser.add_argument(
        "--max-404",
        type=int,
        default=DEFAULT_MAX_404_COUNT,
        help="Stop after > N HTTP 404 responses",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    template = build_url_template(args.url)

    start_time = time.time()
    result = capture_captions(template, args.max_range, args.max_404)

    with open(args.output, "w", encoding="utf-8") as file:
        file.write(result)

    elapsed_minutes = (time.time() - start_time) / 60
    print(f"FINISHED, Time cost: {elapsed_minutes} minutes")


if __name__ == "__main__":
    main()
