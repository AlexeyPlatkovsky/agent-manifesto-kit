---
name: design-converting-to-code
description: Converts a Pencil.dev frame or component into front-end code (HTML/CSS, React, Vue, SwiftUI, Jetpack Compose) using project tokens and existing components. Use when the user asks to implement a design, generate code from a frame, or scaffold a component from a Pencil node.
---

# Converting Design to Code

## When to use

The user wants front-end code generated from a `.pen` design. For creating the design itself, use `design-creating-web-layout` or `design-creating-mobile-layout`. For reviewing a design, use `design-reviewing-ui`.

## Tool constraint

Access `.pen` files only through `pencil` MCP tools.

## Inputs required

- Target framework (React + Tailwind / CSS Modules, Vue, plain HTML/CSS, SwiftUI, Jetpack Compose, etc.)
- Project's component library entry point and token source (CSS variables, theme file, design-tokens JSON)
- Node ID or name of the frame / component to convert
- Output file path

## Procedure

1. Open the document; resolve the node ID via `pencil:snapshot_layout` if only a name is given.
2. Fetch design tokens via `pencil:get_variables`. Build a mapping table: design token → project token.
3. Walk the node tree top-down. For each layer:
   - Map auto-layout to flex / grid in the target framework
   - Map text styles to the project's typography tokens
   - Replace primitive shapes with existing project components when an equivalent exists
4. Generate code that:
   - References project tokens, not literal hex / px values
   - Uses semantic HTML elements (`button`, `nav`, `header`, `main`) where applicable
   - Sets `alt`, `aria-label`, and roles for non-text elements
5. Add a single screenshot via `pencil:get_screenshot` to the code review for visual diff.
6. Run the project's lint / build / Storybook command on the new file.

## Mapping rules

- Auto-layout horizontal → `flex flex-row` / `HStack` / `Row`
- Auto-layout vertical → `flex flex-col` / `VStack` / `Column`
- Spacing tokens → utility classes / theme spacing keys, never raw px
- Fills with token → CSS variable / theme color reference
- Effects (shadow, blur) → token-mapped utility; if no token, flag as needing one
- Text styles → typography component / class; do not inline `font-family`

## Quality checks

- No literal hex, px, or font-family in the generated code.
- Component is responsive within the design's defined breakpoints (web) or scales appropriately (mobile).
- No new tokens introduced silently — if mapping fails, flag a gap.
- Generated code passes lint and type checks.
- Accessibility attributes present on interactive elements.

## Output contract

- Generated file(s) and paths
- Design-to-project token mapping table
- List of unmapped tokens (design has, project lacks) or unmapped components (need a new component)
- Build / lint command result

## Stopping conditions

Stop if:
- The design uses tokens with no project equivalent (ask to extend tokens first)
- A required existing component is not identifiable in the project
- The framework / output path is unspecified
