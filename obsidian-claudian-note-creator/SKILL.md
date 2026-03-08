---
name: obsidian-claudian-note-creator
description: Automatically creates notes in 'fleeting notes/from-claudian' directory when using Claudian or MCP methods. Use this skill whenever the user asks to create a note, write a note, or mentions creating notes through Claudian, MCP, or AI assistance. This ensures all AI-generated notes are organized in a dedicated directory for easy tracking and management.
category: obsidian
---

# Obsidian Claudian Note Creator Skill

This skill automatically directs all notes created through Claudian, MCP, or AI assistance to the `fleeting notes/from-claudian` directory in the Obsidian vault.

## Purpose

When you're working with AI assistants like Claudian or using MCP (Model Context Protocol) tools to create notes in Obsidian, this skill ensures that all such notes are automatically saved to a dedicated directory: `fleeting notes/from-claudian`. This provides:

1. **Organization**: All AI-generated notes are in one place
2. **Tracking**: Easy to see what notes were created by AI assistance
3. **Workflow**: Consistent location for AI-assisted note creation

## When to Use This Skill

Use this skill whenever:
- The user asks to create a new note
- The user asks to write a note
- The user mentions creating notes through Claudian, MCP, or AI assistance
- The user wants to save information to Obsidian
- The user asks to document something in their vault

## How It Works

### Default Behavior
When this skill triggers, it automatically sets the default save location for any new notes to:
```
fleeting notes/from-claudian/
```

### File Naming
1. If the user provides a specific filename, use that name
2. If no filename is specified, generate a descriptive filename based on the note content
3. Use lowercase with hyphens for spaces (e.g., `meeting-notes-2026-03-07.md`)
4. Include date in filename when appropriate (YYYY-MM-DD format)

### Note Structure
When creating notes, follow this structure. All notes must include these four required tags: `ai`, `GenAi`, `generated-by-deepseek`, and `claudian`:

```markdown
---
created: {{current_date}}
source: claudian-ai
tags: [ai, GenAi, generated-by-deepseek, claudian]
---

# [Note Title]

[Note content here]

---
*Created with Claudian AI on {{current_date}}*
```

### Special Cases
1. **If user specifies a different location**: Respect the user's explicit request
2. **If editing existing notes**: Don't move existing notes, only apply to new creations
3. **If the directory doesn't exist**: Create it automatically

## Implementation Steps

When creating a note through this skill:

1. **Check target directory**: Ensure `fleeting notes/from-claudian` exists
2. **Generate filename**: Create appropriate filename if not specified
3. **Set frontmatter**: Include creation date, source, and the required tags: `ai`, `GenAi`, `generated-by-deepseek`, `claudian`
4. **Write content**: Use proper Markdown formatting
5. **Save to directory**: Save to the dedicated AI notes directory

## Examples

### Example 1: Simple note creation
**User**: "Create a note about machine learning basics"
**Action**: Create `fleeting notes/from-claudian/machine-learning-basics.md`

### Example 2: Note with specific title
**User**: "Write a note titled 'Project Ideas for 2026'"
**Action**: Create `fleeting notes/from-claudian/project-ideas-for-2026.md`

### Example 3: Quick capture
**User**: "Save this to Obsidian: 'Meeting with team discussed Q2 goals'"
**Action**: Create `fleeting notes/from-claudian/meeting-notes-2026-03-07.md`

## Directory Structure

The target directory should be organized as:
```
fleeting notes/
└── from-claudian/
    ├── meeting-notes-2026-03-07.md
    ├── project-ideas-2026.md
    ├── machine-learning-basics.md
    └── [other AI-generated notes]
```

## Notes

- This skill only applies to **new note creation** through AI assistance
- Existing notes should not be moved or modified
- The user can always override the default location by specifying a different path
- All notes must include these four required tags: `ai`, `GenAi`, `generated-by-deepseek`, `claudian`
- Additional tags can be added based on note content, but the four required tags must always be present