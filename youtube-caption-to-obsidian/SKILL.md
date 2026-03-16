---
name: youtube-caption-to-obsidian
description: Use this skill when the user wants to turn a YouTube video into an Obsidian note by running the bundled subtitle script first, then using the script output Markdown transcript to write a concise overview.
---

# Workfow Overview
1. run `python youtube-caption-to-obsidian/scripts/srt_generator.py {youtube_url} {output_dir}`  - output_dir is beside the script folder, for example: `youtube-caption-to-obsidian/output/`
2. wait for the script to finish and identify the generated Markdown transcript file from its output
3. read the generated output transcript file, summarize the content, and create an Obsidian note in `fleeting notes/from-claudian` with a link to the generated transcript file for reference.