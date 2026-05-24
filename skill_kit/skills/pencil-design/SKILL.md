---
name: pencil-design
description: Creates and edits UI/UX designs in Pencil via its MCP server. Use for design-only requests. Do not implement application code for design-only tasks.
---

# Pencil Design

## What Is Pencil

[Pencil](https://pencil.dev) is a UI/UX design tool for creating web and mobile mockups. Designs are stored as encrypted `.pen` files and can only be read or edited through the Pencil MCP server — never with standard file tools like Read or Grep.

## Prerequisites

The Pencil MCP server must be configured and running in your Claude Code settings. If MCP tools like `get_editor_state` are unavailable, stop and ask the user to configure the Pencil MCP server before continuing.

## When To Use

Use for design requests such as "Design the upload page" or "Rework the dashboard layout."
Do not edit application code, HTML, CSS, or JS for design-only requests.

## Workflow
1. Check editor state: `get_editor_state(include_schema=true)`
2. Inspect existing designs with `batch_get` before making any changes.
3. Retrieve relevant design guidelines using `get_guidelines` for the project type (web-app, mobile-app, landing-page, etc.).
4. Consult available project brand, design guide, or UI documentation before major changes.
5. Apply changes using `batch_design` with meaningful node names and proper sibling ordering.
6. Verify changes via `get_screenshot` and `batch_get`.

## Pencil MCP Tool Reference

All tools below are MCP server commands provided by the Pencil MCP server.

| Tool | What it does |
| --- | --- |
| `get_editor_state(include_schema=true)` | Returns the current document structure and available node types/properties |
| `open_document(path)` | Opens a `.pen` file from the `.pencil/` directory |
| `batch_get(node_ids)` | Reads current properties of one or more nodes — always inspect before editing |
| `get_guidelines(project_type)` | Returns design rules for the project type (e.g., `web-app`, `mobile-app`, `landing-page`) |
| `batch_design(operations)` | Applies create, update, or delete operations to nodes |
| `get_screenshot()` | Captures the current canvas as an image — use to verify changes visually |
| `snapshot_layout()` | Records the current layout state for comparison |
| `get_variables()` / `set_variables()` | Reads or writes design tokens (colors, spacing, typography) |
| `find_empty_space_on_canvas()` | Locates free space for placing new elements |
| `search_all_unique_properties(property)` | Finds all distinct values of a property across the document |
| `replace_all_matching_properties(...)` | Bulk-updates a property value across matching nodes |
| `export_nodes(node_ids, format)` | Exports nodes as PNG, SVG, or other formats |

## Critical Rules

- All `.pen` files live in `.pencil/` — never read `.pen` files with standard file tools.
- Use Pencil MCP tools exclusively for `.pen` file operations.
- Name all significant nodes by purpose, not primitive type: "Settings Panel" not "Frame 3".
- Pencil renders siblings in reverse order in the Layers tab — order bottom-to-top, right-to-left when that matters.
- When the target screen or implementation scope is unclear, ask one clarifying question before proceeding.
