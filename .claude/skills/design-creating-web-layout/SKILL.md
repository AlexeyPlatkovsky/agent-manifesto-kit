---
name: design-creating-web-layout
description: Creates a responsive web screen layout in Pencil.dev using auto-layout, design tokens, and grid systems for desktop, tablet, and mobile breakpoints. Use when the user asks to design a web page, dashboard, or marketing site screen.
---

# Creating a Web Layout

## When to use

The user wants a new web-screen design in Pencil. For mobile-app screens use `design-creating-mobile-layout`. For reviewing an existing design use `design-reviewing-ui`. For tokens / system, use `design-creating-design-system`.

## Tool constraint

`.pen` files are accessed only through `pencil` MCP tools — never via Read or Bash.

## Inputs required

- Screen purpose and primary user action
- Target breakpoints (default: 1440 / 1024 / 768 / 375)
- Existing design system (`pencil:get_variables`, `pencil:get_guidelines`)
- Reference content or copy

## Procedure

1. Open or create the target document (`pencil:open_document`).
2. Fetch tokens (`pencil:get_variables`) and guidelines (`pencil:get_guidelines`). If missing, ask whether to define them first via `design-creating-design-system`.
3. Find empty canvas space (`pencil:find_empty_space_on_canvas`).
4. Build the desktop frame first at the largest breakpoint:
   - Use a 12-column grid with the project's gutter / margin tokens
   - Apply auto-layout to all containers; no free-floating elements
   - Use token-based spacing (4/8 base scale) — no arbitrary px values
   - Use semantic text styles (display / heading / body / caption)
5. Compose regions in order: header → hero / primary content → secondary content → footer.
6. Create breakpoint variants by duplicating and reflowing — do not redesign:
   - Tablet: collapse 12 cols to 8 or stack
   - Mobile: single column, larger tap targets (min 44 px), sticky CTA where relevant
7. Apply components from the library instead of new ad-hoc shapes.
8. Snapshot layout (`pencil:snapshot_layout`) and screenshot (`pencil:get_screenshot`) for review.

## Quality checks

- Every color, spacing, and text style maps to a variable.
- No magic spacing values (off the scale).
- Auto-layout used; no absolute-positioned children inside layout regions.
- Tap targets meet minimum size on the mobile variant.
- Hierarchy: one primary action per screen; secondary actions visibly subordinate.
- Empty / loading / error states either present or explicitly deferred.

## Output contract

- IDs and names of the new frames per breakpoint
- Components used vs newly created
- List of any new tokens introduced (should be zero unless `design-creating-design-system` was triggered)
- Screenshot link/path
- Open questions for the user

## Stopping conditions

Stop if:
- Design system tokens are not present
- The screen requires interactions or motion specs beyond static layout
- Content is undefined and the user has not approved using placeholder copy
