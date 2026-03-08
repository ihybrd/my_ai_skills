---
name: gdc-vtt-to-note
description: When the user provides a GDC VTT segment URL, run the bundled capture script to merge captions, then summarize and create an Obsidian note under gdc summary.
---

# GDC VTT To Note Skill

## Purpose
Use this skill when a user wants to turn a GDC talk caption stream into:
1. A merged caption file.
2. A short structured summary.
3. An Obsidian note in `fleeting notes/from-claudian`.

## Trigger
- User provides a GDC caption `.vtt` segment URL.

## Required Input
- One GDC VTT segment URL, for example: `.../index_4_0_33.vtt`

## Do not
download the provided vtt file directly, instead, run the bundled script to process it and generate a caption file (captions.txt). Then read the generated caption file to create the summary and note.

## Script Execution
run the script with the provided VTT segment URL. For example:
`python3 gdc-vtt-to-note/scripts/capture_gdc_vtt.py $vtt_url_provided_by_user`

## Post-Processing Workflow
this section will be exectuted only when the script stops running and generates a caption file (captions.txt). If the script fails, report the error and do not proceed.

once the script successfully generates a caption file (captions.txt), do the following:

1. Read the generated caption file.
2. Build a concise summary including:
   - Topic
   - Key points
   - Actionable insights
3. Create an Obsidian note in `fleeting notes/from-claudian`.

## Note Naming Rule
- Filename format: `YYYY-MM-DD-{summary_slug}.md`
- Slug rules:
  - lowercase
  - spaces -> `-`
  - remove invalid filename characters
- If conflict exists, append `-2`, `-3`, etc.

## Note Content
Include:
- Title
- Source VTT URL
- Caption file path
- Summary sections
- Captions.txt full content as reference

Prefer frontmatter metadata:
- `source_vtt`
- `caption_file`
- `created_at`
- `tags: [gdc, summary]`

## Safety
- If script execution fails, report stderr and do not create the note.
- If caption file is empty, create note with `incomplete` status.
- Prefer absolute paths in command execution and output reporting.
