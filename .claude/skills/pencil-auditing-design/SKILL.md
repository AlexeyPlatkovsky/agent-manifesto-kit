---
name: pencil-auditing-design
description: Audits a Pencil.dev .pen design for inconsistencies in tokens, components, spacing, and naming. Use when the user asks to review, audit, lint, or check the quality of a Pencil design before handoff or implementation.
---

# Auditing a Pencil Design

## When to use

The user wants a quality review of an existing `.pen` design — finding inconsistent styles, off-token values, broken components, or naming issues. Not for opening (`pencil-opening-design`) or exporting (`pencil-exporting-assets`).

## Tool constraint

Operate on `.pen` files only through `pencil` MCP tools.

## Preconditions

- Document is open. If `pencil:get_editor_state` returns no active document, run `pencil-opening-design` first, then return here.
- Variables and guidelines have been fetched.

## Audit checklist

Run these checks in order and record findings:

1. **Variable usage**
   - Call `pencil:get_variables` and `pencil:search_all_unique_properties` for colors, fontFamily, fontSize, spacing.
   - Flag any literal value that does not match a defined variable.

2. **Component reuse**
   - Identify visually similar but unlinked frames (candidates for componentization).
   - Flag detached instances of registered components.

3. **Naming**
   - Frame and layer names should be human-readable, not `Frame 23`, `Group 8`.
   - Component names should be unique per page.

4. **Spacing and alignment**
   - Flag spacing values not on the project's spacing scale.
   - Flag misaligned siblings within the same auto-layout container.

5. **Guideline compliance**
   - Cross-check `pencil:get_guidelines` output against current state.

6. **Accessibility**
   - Flag text/background pairs that likely fail WCAG AA contrast (note as "needs verification", do not compute color math yourself).
   - Flag text smaller than the project's minimum body size.

## Output contract

Produce a findings table:

| Severity | Area | Frame/Component | Issue | Suggested fix |
| --- | --- | --- | --- | --- |

Severities: Blocking, Major, Minor, Info.

End with a one-paragraph verdict: ready for handoff / needs revision / blocked.

## Stopping conditions

Stop if the document has no guidelines or variables defined — ask the user whether to audit against generic defaults or to skip those checks.
