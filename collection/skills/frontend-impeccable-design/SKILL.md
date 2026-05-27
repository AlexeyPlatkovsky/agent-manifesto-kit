---
name: frontend-impeccable-design
description: Generate a new frontend UI from a brief with a deliberate, distinctive aesthetic — components, pages, landing surfaces, dashboards, or app shells. Use when the user asks to design, build, create, scaffold, or generate UI code from scratch or from a description. Do not use for polishing already-built UI, accessibility or technical audits, or design-tool work in encrypted design files (e.g., `.pen`).
---

## Scope

- Generate new UI as real code (HTML/CSS/JS, React, Vue, Svelte, or the project's existing framework).
- Commit to a single distinctive aesthetic direction per surface.
- Avoid generic "AI made this" defaults in font, color, layout, and motion choices.

## Prerequisites

- A brief from the user: purpose, audience, surface (component / page / app shell), and any technical constraints (framework, dark/light, target devices).
- Ability to write source files into the target project.
- If the project has brand context files (e.g., `PRODUCT.md`, `DESIGN.md`, brand guidelines), read them before designing. If none exist, infer the register (brand surface vs product UI) from the brief and state the inference in the report.
- If the project has an existing component library, design system, or shared tokens, read them before generating new components; reuse rather than duplicate where the existing primitive fits.

## Safety Constraints

- Do not modify backend, data, or auth code. UI code only.
- Do not invent product copy that asserts facts about real entities, prices, dates, claims, or legal text. Use clearly placeholder copy or ask the user for real strings.
- Do not introduce new heavyweight dependencies (animation libraries, design systems, icon kits) without first checking what the project already uses; prefer the existing stack.
- When generating a surface that resembles an existing one, do not silently overwrite the existing file. Stop and confirm intent.

## Procedure

### 1. Read the brief and the project

- Restate the brief in one sentence to confirm understanding: who uses this surface, where, under what conditions.
- Identify the register: brand (marketing, landing, campaign — design IS the product) or product (app UI, dashboard, tool — design SERVES the product).
- Locate the project's framework, existing components, token system, fonts in use, and any global styles. Use what is there.

### 2. Commit to a direction before generating

State, in the report, a single aesthetic direction in plain words. Examples: brutally minimal, editorial-typographic, terminal-native, soft pastel, industrial-utilitarian, art deco geometric, retro-futuristic. Do not generate two directions in parallel as alternatives unless the user asked for variants.

### 3. Apply the design laws

These laws apply to every generated surface, both registers. Match implementation complexity to the chosen direction — maximalist needs elaborate code, minimalist needs precision.

**Color**
- Use OKLCH for new color values. Reduce chroma as lightness approaches 0 or 100.
- Never use literal `#000` or `#fff`. Tint neutrals toward the brand hue (chroma ~0.005–0.01).
- Pick a color strategy before picking colors: restrained (one accent ≤10%), committed (one color carries 30–60%), full palette (3–4 named roles), or drenched (the surface IS the color). State the choice.

**Theme**
- Dark vs light is never a default. Write one sentence describing the physical scene (who, where, ambient light, mood). If that sentence does not force the answer, add detail until it does.

**Typography**
- Pair a distinctive display font with a refined body font. Avoid Inter, Roboto, Arial, and system-default-only stacks unless the chosen direction explicitly calls for them.
- Cap body line length at 65–75ch. Enforce ≥1.25 ratio between hierarchy steps.

**Layout**
- Use the layout that fits the content, not the layout reflex of the category. Asymmetry, overlap, generous negative space, and controlled density are all permitted; pick one.
- Cards are the lazy answer. Use them only when they are the best affordance for the content. Nested cards are always wrong.

**Motion**
- Animate transform and opacity. Do not animate CSS layout properties (width, height, top, left, margin).
- Ease-out with exponential curves. No bounce or elastic easing by default.

**Copy**
- Every word earns its place. No restated headings. No em dashes (or `--`); use commas, colons, semicolons, periods, or parentheses.

### 4. Avoid AI-slop defaults

Do not generate these as defaults. If the chosen direction genuinely calls for one, justify it in the report.

- Side-stripe borders: `border-left`/`border-right` >1px as a colored accent on cards or alerts.
- Gradient text: `background-clip: text` combined with a gradient fill.
- Decorative glassmorphism as a default surface treatment.
- Hero-metric template: big number + small label + supporting stats + gradient accent.
- Identical card grids: same-sized icon + heading + text repeated as the page's primary layout.
- Modal-first interaction reflex.
- Purple-gradient-on-white, navy-and-gold-fintech, dark-blue-observability, neon-on-black-crypto, and other category-reflex palettes.

### 5. Category-reflex check before generating

Ask: could someone guess the theme and palette from the product category alone? If yes, rework the scene sentence and color strategy until the answer is not obvious. Run this check before writing code, not after.

## Stop Triggers

Stop and ask the user instead of generating when any of the following apply:

- The brief is missing purpose, audience, or surface and cannot be inferred from project context.
- A surface with the same path or name already exists and would be overwritten.
- The required framework or token system is unclear and the project has multiple candidates.
- More than one materially distinct aesthetic direction is viable for the same brief and the choice matters. Present options with one-line trade-offs and let the user choose.

## Verification

After generating:

- Confirm each new file compiles or type-checks if the project has those gates available.
- Render the surface in a dev server or preview if one is reasonably available; confirm it loads without obvious regression. If not available, state that visual verification was skipped.
- Re-read each new file against the design laws and AI-slop list to confirm nothing was reintroduced by reflex.

## Output Contract

Emit:

`Skill: frontend-impeccable-design - output below`

Then include:

### Brief Restated

One sentence: who, where, under what conditions.

### Direction

| Field | Value |
| --- | --- |
| Register | brand / product |
| Aesthetic direction | one short phrase |
| Color strategy | restrained / committed / full palette / drenched |
| Theme | light / dark, with the scene sentence that forced it |
| Display font | name + rationale |
| Body font | name + rationale |

### Files Generated

List each new file with a one-line description of what it contains.

### Verification

State which verification steps ran and their result, including any that were skipped and why.

### Open Choices

For each choice deliberately left to the user: option, recommendation, trade-off. Empty list if none.

## Attribution

See `collection/NOTICE.md` for attribution.
