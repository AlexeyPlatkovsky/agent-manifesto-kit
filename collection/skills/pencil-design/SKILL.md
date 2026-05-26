---
name: pencil-design
description: Creates and edits UI/UX designs in Pencil via its MCP server. Use for design-only requests. Do not implement application code for design-only tasks.
---

## Scope

- Create and edit UI/UX designs in Pencil for design requests such as "Design the upload page" or "Rework the dashboard layout."

## What Is Pencil

[Pencil](https://pencil.dev) is a UI/UX design tool for creating web and mobile mockups. Designs are stored as encrypted `.pen` files and can only be read or edited through the Pencil MCP server — never with standard file tools like Read or Grep.

## Prerequisites

The Pencil MCP server must be installed, configured, and running in your Claude Code settings. Verify availability by confirming Pencil MCP tools such as `get_editor_state` and `get_guidelines` are callable. If they are unavailable, stop and ask the user to configure the Pencil MCP server before continuing.

## Safety Constraints

- Never read `.pen` files with standard file tools; use the active Pencil document or a user-provided absolute `.pen` path through Pencil MCP tools.
- Use Pencil MCP tools exclusively for `.pen` file operations.
- Name all significant nodes by purpose, not primitive type: "Settings Panel" not "Frame 3".
- Pencil renders siblings in reverse order in the Layers tab — order bottom-to-top, right-to-left when that matters.
- For larger designs, split `batch_design` work by logical section. Avoid large insert operations with many descendants; prefer helper functions, loops, and smaller batches.

## Procedure

1. Check editor state: `get_editor_state(include_schema=true)`.
2. Before opening a document, call `open_document(path)` only when the user requested a specific `.pen` file and an absolute path is available; call `open_document()` with no path only when no active editor is open.
3. Inspect existing designs with `batch_get` before making any changes.
4. Retrieve relevant design guidelines using `get_guidelines` by category, name, and required params.
5. Consult available project brand, design guide, or UI documentation before major changes.
6. Call `snapshot_layout` to record the current state, then apply changes using `batch_design` with meaningful node names and proper sibling ordering.
7. Verify changes via `get_screenshot`, `batch_get`, and a post-change `snapshot_layout` when visual layout changes were made.

If the target file, frame, screen, or implementation scope is unclear, ask one concise clarification before editing.

## Error Handling

If `batch_design` fails, report the error; the failed operation batch is rolled back. If `batch_design` returns warnings, fix them in the next batch before proceeding to broader visual verification.

## Pencil MCP Tool Reference

All tools below are MCP server commands provided by the Pencil MCP server.

| Tool | What it does |
| --- | --- |
| `get_editor_state(include_schema=true)` | Returns the current document structure and available node types/properties |
| `open_document(path)` | Opens a user-requested `.pen` file by absolute path; omit `path` only to open a new document when no active editor exists |
| `batch_get(nodeIds, patterns, parentId, readDepth, ...)` | Reads current properties of one or more nodes or searches by pattern — always inspect before editing |
| `get_guidelines(category, name, params)` | Lists or loads Pencil guides and styles |
| `batch_design(filePath, input)` | Applies JavaScript snippets that create, update, move, replace, or delete nodes |
| `get_screenshot(nodeId)` | Captures a node as an image; use `document` for the whole document |
| `snapshot_layout()` | Records the current layout state for comparison |
| `get_variables()` / `set_variables()` | Reads or writes design tokens (colors, spacing, typography) |
| `find_empty_space_on_canvas()` | Locates free space for placing new elements |
| `search_all_unique_properties(property)` | Finds all distinct values of a property across the document |
| `replace_all_matching_properties(...)` | Bulk-updates a property value across matching nodes |
| `export_nodes(nodeIds, format)` | Exports nodes as PNG, JPEG, WEBP, or PDF |

## Verification

Before reporting completion, verify that layout problems are absent or explained using post-change `snapshot_layout` when visual layout changed, significant edited nodes can be read back with `batch_get`, and a screenshot was captured for visual changes unless unavailable.

## Output Contract

Emit:

`Skill: pencil-design - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed`, `skipped`, or `blocked` |
| Target | Document, page, frame, or node area changed |
| Files changed | `.pen` files created or modified |
| Changes made | Design elements created, updated, or deleted |
| Guidelines used | Pencil guidelines, style, or project design source consulted |
| Verification | `snapshot_layout`, `batch_get`, screenshot path, or reason not run |
| Assumptions / inferred decisions | Material assumptions or inferred design decisions, or `none` |
| Warnings / Errors | Tool warnings or errors, or `none` |
| Open questions | Clarifications needed, or `none` |
