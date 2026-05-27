---
name: frontend-impeccable-polish
description: Final-pass visual and interaction polish for an already-built frontend UI before shipping. Use when the user asks to polish, refine, tighten, or clean up a built-out interface — typography rhythm, spacing, color discipline, motion, copy, and removal of generic "AI made this" tells. Do not use for initial design from scratch, accessibility audits, or performance work.
---

## Scope

- Tighten an already-built UI surface: typography, spacing, color, motion, copy.
- Replace generic patterns with committed aesthetic choices.
- Remove "AI made this" tells.

## Prerequisites

- A target identified by the user: a route, component file, directory, or screenshot.
- Ability to edit source files in the target's project.
- If the project has brand context files (e.g., `PRODUCT.md`, `DESIGN.md`, brand guidelines), read them before editing. If none exist, infer the register from the surface in focus and state the inference in the report.

## Safety Constraints

- Never run this skill on initial-design tasks. If the target is empty, a wireframe, or unbuilt, stop and tell the user this skill polishes existing UI only.
- Never change behavior or component contracts while polishing. Visual and copy changes only. If a polish requires a behavior change, stop and surface the options to the user.
- Do not modify or remove accessibility attributes or ARIA semantics. The only allowed change is fixing an obvious regression that another polish edit would otherwise introduce. If the user asks for ARIA or a11y changes, stop and direct them to a dedicated accessibility audit.

## Procedure

Work each section in order. Skip a section only if it does not apply to the target; record the skip and the reason in the report.

### 1. Color

- Replace literal `#000` and `#fff` with neutrals tinted toward the brand hue (in OKLCH, chroma ~0.005–0.01).
- Reduce chroma as lightness approaches 0 or 100.
- Identify and state the color strategy actually in use: restrained (one accent ≤10%), committed (one color carries 30–60%), full palette (3–4 named roles), or drenched. If the surface is incoherent across strategies, pick one and align to it.

### 2. Typography

- Cap body line length at 65–75ch.
- Enforce a ≥1.25 ratio between hierarchy steps. Rewrite flat scales.
- Carry hierarchy through size and weight, not color.

### 3. Layout

- Vary spacing for rhythm; remove uniform padding repeated across unrelated regions.
- Remove card wrappers that serve no affordance. Eliminate nested cards.
- Drop container wrappers that impose no real constraint.

### 4. Motion

- Replace animations of layout properties (width, height, top, left, margin) with transform/opacity equivalents.
- Use ease-out exponential curves. Remove bounce and elastic easing.

### 5. Copy

- Cut restated headings and intros that repeat the title.
- Replace em dashes (and `--`) with commas, colons, semicolons, periods, or parentheses.
- Tighten labels and error messages to single concrete actions.

### 6. AI-slop removal

If any of the following appear in the target, rewrite the element rather than tweaking it:

- Side-stripe borders: `border-left`/`border-right` greater than 1px used as a colored accent on cards, list items, callouts, or alerts.
- Gradient text: `background-clip: text` combined with a gradient fill.
- Decorative glassmorphism used as a default surface treatment.
- Hero-metric template: big number + small label + supporting stats + gradient accent.
- Identical card grids: same-sized icon + heading + text repeated as the page's primary layout.
- Modal as the first reach for a workflow that could be inline or progressive.

### 7. Category-reflex check

Before reporting done, ask whether someone could guess the surface's theme and palette from the product category alone (e.g., observability → dark blue, healthcare → white + teal, fintech → navy + gold, crypto → neon on black). If yes, the polish has not escaped the training-data reflex. Rework color and theme until the answer is not obvious from the domain.

## Stop Triggers

Stop and report instead of editing when any of the following apply:

- The target does not exist, is empty, or is not yet implemented.
- The requested change requires behavior or contract changes rather than visual polish.
- Brand context files are present but conflict with each other; surface the conflict.
- More than one materially valid polish option exists for the same element. Continue unrelated unambiguous work first, then present deferred cases with options, recommendation, and trade-off at the end for the user to choose.

## Verification

After edits:

- Confirm each changed file still compiles or type-checks if the project has those gates available.
- Re-read each changed region against this skill's sections to confirm no banned pattern was reintroduced.
- If a dev server or preview is reasonably available, run it and confirm the affected surface renders without obvious regression. If not available, state that visual verification was skipped.

## Output Contract

Emit:

`Skill: frontend-impeccable-polish - output below`

Then include:

### Sections Applied

| Section | Status | Notes |
| --- | --- | --- |

`Status` is one of: Applied, Skipped (not applicable), Skipped (no occurrences), Deferred (ambiguous).

### Changes

List each changed file with a one-line description of the polish applied.

### Deferred Ambiguities

For each deferred case: target, options considered, recommendation, trade-off. Empty list if none.

### Verification

State which verification steps ran and their result, including any that were skipped and why.

## Attribution

See `collection/NOTICE.md` for attribution.
