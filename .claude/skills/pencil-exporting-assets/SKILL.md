---
name: pencil-exporting-assets
description: Exports nodes, frames, or screenshots from an open Pencil.dev .pen file to image or vector assets. Use when the user asks to export a design, render a frame to PNG/SVG, or extract assets from a Pencil document.
---

# Exporting Pencil Assets

## When to use

The user wants visual assets out of a `.pen` design (PNG, SVG, screenshots of specific frames or components). Not for inspecting structure or generating code from a design.

## Tool constraint

`.pen` files are encrypted. Use only `pencil` MCP tools. Never read the binary file directly.

## Preconditions

- Document is opened (via `pencil:open_document`).
- Target node IDs are known. If not, call `pencil:get_editor_state` or `pencil:snapshot_layout` first to enumerate them.
- The output directory exists and is writable.

## Procedure

1. Confirm with the user:
   - Output directory (absolute path)
   - Format (PNG, SVG, JPG)
   - Resolution / scale (1x, 2x, 3x)
   - Naming convention (frame name, ID, custom prefix)
2. For specific named nodes, call `pencil:export_nodes` with the resolved node IDs.
3. For a visual preview of the canvas state, call `pencil:get_screenshot`.
4. Verify each expected file exists on disk after export.
5. Report any nodes that failed to export with the reason from the tool output.

## Output contract

- Table of: node id, node name, output path, format, size
- Count of successful vs failed exports
- Suggested next step (e.g., "open in design tool", "feed to code generator")

## Stopping conditions

Stop and ask if:
- The document is not open
- Node IDs cannot be resolved from the names the user gave
- The output directory does not exist (do not create it without approval)
- Format requested is not supported by `export_nodes`
