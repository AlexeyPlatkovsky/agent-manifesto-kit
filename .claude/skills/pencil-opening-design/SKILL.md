---
name: pencil-opening-design
description: Opens a .pen design file in Pencil.dev and produces a structured summary of its frames, components, and variables. Use when the user references a .pen file, asks to inspect a Pencil design, or wants an overview of a design's structure before editing.
---

# Opening a Pencil Design

## When to use

The user wants to inspect or load an existing `.pen` file. Not for creating new designs (`design-creating-web-layout`, `design-creating-mobile-layout`) or generating code from a design (`design-converting-to-code`).

## Tool constraint

`.pen` files are encrypted. They MUST be accessed through `pencil` MCP tools only. Do NOT use Read, Grep, Bash `cat`, or any filesystem tool on a `.pen` file.

## Procedure

1. Confirm the absolute path of the `.pen` file with the user.
2. Call `pencil:open_document` with that path.
3. Call `pencil:get_editor_state` to confirm the document loaded and to identify the root document/page IDs.
4. Call `pencil:get_guidelines` to fetch any design-system guidance attached to the document.
5. Call `pencil:get_variables` to enumerate design tokens (colors, spacings, typography, etc.).
6. Call `pencil:snapshot_layout` on the top-level frames to capture structure without loading every node.
7. Optionally call `pencil:get_screenshot` for visual context if the user asked for a preview.

## Output contract

Produce a single summary message containing:
- Document name and path
- List of top-level pages/frames (id + name)
- Count of components, variables, and unique styles
- Any guideline notes that affect editing
- Next-step suggestion (e.g., "ready for editing", "components missing", "tokens incomplete")

Do NOT dump raw tool output. Summarize.

## Stopping conditions

Stop and ask the user if:
- `open_document` returns an error (corrupt file, wrong version)
- The document is empty or unrecognizable
- The user has not specified which `.pen` file to open
