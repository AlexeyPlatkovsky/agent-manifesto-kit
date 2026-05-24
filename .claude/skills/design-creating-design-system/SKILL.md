---
name: design-creating-design-system
description: Defines or extends a foundational design system in Pencil.dev — color, typography, spacing, radius, elevation tokens and a core component set. Use when the user asks to create a design system, set up tokens, build foundations, or scaffold a component library in Pencil.
---

# Creating a Design System

## When to use

The user wants to define foundational tokens and a core component set in a Pencil document. For applying an existing system to a screen, use `design-creating-web-layout` or `design-creating-mobile-layout`. For auditing, use `pencil-auditing-design`.

## Tool constraint

Access `.pen` files only via `pencil` MCP tools.

## Inputs required

- Document target (new or existing `.pen`)
- Brand inputs: primary color(s), font family, target platforms (web, iOS, Android)
- Light / dark mode requirement
- Existing tokens to preserve (`pencil:get_variables`)

## Token scope

Define tokens in this order. Each must have a semantic name (`color/surface/default`), not a literal (`color/blue-500`).

1. **Color**
   - Primitive palette: 11-step ramps for brand + neutrals
   - Semantic tokens: surface, content, border, brand, success, warning, danger, info — each with default / muted / strong variants
   - Mode pairs: light + dark
2. **Typography**
   - Font family (sans, serif, mono) tokens
   - Type scale: display, h1–h4, body, body-sm, caption, code — each with size, line-height, weight, letter-spacing
3. **Spacing** — 4 px base scale (0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24)
4. **Radius** — none, sm, md, lg, full
5. **Elevation** — 0–5 shadow tokens
6. **Border** — width + style tokens
7. **Motion** (notes only) — duration and easing tokens for handoff

## Core components

After tokens, define this minimal set, each in default / hover / focus / disabled states:

- Button (primary, secondary, ghost, destructive — sm/md/lg)
- Input (text, with label, helper, error)
- Select / dropdown trigger
- Checkbox, Radio, Switch
- Card
- Modal / Dialog
- Toast / Snackbar
- Tabs
- Navigation (top bar, side nav)
- Icon container (sm/md/lg)

## Procedure

1. Fetch current state (`pencil:get_variables`, `pencil:get_guidelines`). Reuse what exists.
2. Call `pencil:set_variables` to add missing tokens in the order above. Use `pencil:replace_all_matching_properties` to migrate literal values that should now be tokens.
3. Build each core component on a dedicated page, with all states laid out.
4. Document guidelines next to each component: when to use, when not to, do / don't.
5. Snapshot for review.

## Quality checks

- Semantic names only; no `blue` in semantic layer
- Light + dark token pairs complete
- Type scale renders legibly on smallest target device
- Components use tokens for every color, spacing, radius, and text style
- Each component has all interactive states defined

## Output contract

- List of tokens added or updated (name + value + mode)
- Components built with their page locations
- Migration report from `replace_all_matching_properties` if used
- Open gaps (e.g., motion still undefined)

## Stopping conditions

Stop if:
- Brand inputs are missing
- Existing tokens conflict with the new semantic names (ask before overwriting)
- Light / dark mode requirement is unclear
