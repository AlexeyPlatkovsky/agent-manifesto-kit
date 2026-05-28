---
name: frontend-audit
description: Diagnostic review of an existing frontend UI for accessibility, responsive behavior, semantic structure, color contrast, and obvious performance hazards. Reports findings with severity; does not edit code unless the user explicitly asks for fixes. Use when the user asks to audit, review for a11y, check responsive, review semantics, or assess UI quality. Do not use for visual polish or initial design.
---

## Scope

- Diagnose an existing UI surface (route, component, directory, or rendered screenshot) and report issues with severity.
- Cover accessibility per WCAG 2.2 AA success criteria by default, plus keyboard navigation, ARIA correctness, semantic HTML, color contrast, responsive behavior across common breakpoints, image and asset handling, and obvious performance hazards. If the project documents a different target (e.g., 2.1 AA, 2.2 AAA, or named exceptions), follow that instead and state the standard used in the report.

## Prerequisites

- A target identified by the user: a route, file, directory, or screenshot.
- Ability to read source files in the target.
- This skill is guide-only — it does not invoke axe-core, Lighthouse, or external tooling. If the user wants tool-based output, they should run those tools separately and feed results in.
- Default standard is WCAG 2.2 AA. If the project documents a different conformance target or design-system accessibility contract, read it before judging and use it in place of the default. State the standard used in the Scope Audited table.

## Safety Constraints

- Do not edit code as part of the audit. The output is a report. The user may request fixes in a follow-up; fixes belong to a visual-polish pass (for visual issues) or a code-edit pass (for behavioral issues), not to this skill.
- Do not claim WCAG conformance levels (A / AA / AAA) without checking each criterion under that level. State only the criteria actually checked.
- Do not infer behavior from class names alone. For runtime-only findings, apply the label-only Stop Trigger (see Stop Triggers).

## Procedure

Attempt each section in order. If a halt-class Stop Trigger fires (see Stop Triggers below), stop the audit immediately and return a halted report naming the trigger — do not continue with remaining sections. Otherwise, for sections that do not apply to the located target, skip and record the reason in the Coverage section. Per-finding ambiguity (e.g., runtime-only behavior) attaches to the affected finding via the severity enum and does not halt the audit.

### 1. Semantic structure

- Confirm a single `<h1>` per page; heading levels do not skip downward (no `<h1>` → `<h3>`).
- Landmarks present and used correctly: `<header>`, `<nav>`, `<main>`, `<footer>`, `<aside>`. No duplicated landmarks without `aria-label`.
- Lists use `<ul>` / `<ol>` / `<li>`. Buttons are `<button>`, links are `<a href>`. Do not accept `<div onClick>` for interactive elements.
- Form fields have associated `<label>` (explicit `for=` or wrapping). Error messages associated via `aria-describedby`.

### 2. Keyboard and focus

- Every interactive element is reachable by `Tab` in a logical order.
- Visible focus indicator exists and is not removed by `outline: none` without a replacement.
- No keyboard trap inside dialogs, popovers, or menus. Dialogs return focus to the trigger on close.
- Custom widgets implement the expected key bindings (Esc closes a dialog, arrow keys navigate a menu, Space/Enter activate a button).

### 3. ARIA correctness

- ARIA attributes are used only where native semantics are insufficient. No `role="button"` on a `<button>`.
- `aria-label`, `aria-labelledby`, and `aria-describedby` reference existing ids and convey real information, not redundant text.
- Live regions (`aria-live`) are present for asynchronous status updates and not used to announce every render.
- `aria-hidden="true"` is never applied to an element that contains focusable descendants.

### 4. Color and contrast

- Body text against its background meets WCAG 1.4.3 (4.5:1 for normal text, 3:1 for large text).
- Non-text UI affordances (focus rings, input borders, icon-only buttons) meet WCAG 1.4.11 (3:1 against adjacent colors).
- Information is not conveyed by color alone (errors are not only red; status is not only green).

### 5. Responsive behavior

- Layout works at 320px, 768px, 1024px, and 1440px without horizontal scroll on the body.
- Touch targets are at least 24x24 CSS px (WCAG 2.5.8); 44x44 for primary actions where reasonable.
- Text reflows; no fixed pixel widths on text containers that would clip at common widths.
- Sticky and fixed elements do not cover essential content on small viewports.

### 6. Images and media

- Every `<img>` has an `alt` attribute. Decorative images use `alt=""`. Informative images have meaningful alt text, not the filename.
- `<img>` declares `width` and `height` (or aspect-ratio) to prevent layout shift.
- Video and audio have captions or transcripts when content is non-decorative.

### 7. Performance hazards (source-visible only)

- No render-blocking inline scripts in `<head>` for non-critical work.
- Images use modern formats (AVIF/WebP) or have a documented reason not to.
- No obvious oversize bundles imported for one-off uses (e.g., importing all of lodash for one function).
- No layout-thrashing animations (animating width/height/top/left); flag these as also failing the polish rule.

## Stop Triggers

Triggers below have different effects. Apply each per its category.

**Halt the audit and return a halted report naming the trigger:**

- The target cannot be located or read.

**Continue the audit, but downgrade or withhold severity claims:**

- The applicable WCAG conformance target or design-system contract is unclear and would change the severity of multiple findings. Do not assign Blocker or Major to affected findings; record them at Minor or Info with the reason, and recommend re-audit after the contract is clarified. (Operationalizes the conformance-claim restriction in Safety Constraints for the unclear-target case.)

**Continue the audit; label only the affected finding:**

- A finding requires runtime behavior that source-only inspection cannot confirm. Mark it `Requires runtime verification` per the severity enum.

## Verification

This skill produces a report, not edits. Verification:

- Confirm every finding cites a concrete file and line, attribute, selector, or screenshot region.
- Confirm severity is assigned per the scale below, not by intuition.
- Confirm the section coverage table records each procedure section as covered, skipped (not applicable), or skipped (no occurrences).

## Output Contract

Emit:

`Skill: frontend-audit - output below`

Then include:

### Scope Audited

| Target | Sections Covered | Sections Skipped |
| --- | --- | --- |

### Findings

| ID | Section | Severity | Location | Issue | Suggested fix |
| --- | --- | --- | --- | --- | --- |

Severity values:

- **Blocker**: violates a documented WCAG criterion at the level the project claims to meet, or breaks keyboard access entirely.
- **Major**: significant a11y, responsive, or semantic issue likely to affect real users.
- **Minor**: smaller issue, low user impact, worth fixing on the next pass.
- **Info**: observation that is not a violation but worth recording.
- **Requires runtime verification**: finding suspected from source but unconfirmable without running the surface.

### Coverage

State which procedure sections ran and which were skipped, with the reason for each skip.

### Recommended Next Step

A single concrete next step: a fix pass, a runtime verification pass, or a re-audit after specific changes.

## Attribution

See `collection/NOTICE.md` for attribution.
