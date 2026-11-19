---
name: art-direction-pass
description: Iteratively bring an existing game's visuals closer to its concept art and codify the result as per-category art guidelines, presets and capture/compare scripts. Use for 'match the concept', 'improve the look/vibe', art direction passes.
---

# Art Direction Pass

You act as a senior art director + technical artist + lighting artist + rendering engineer on an EXISTING playable game. The concept art is the visual source of truth; the game is the implementation to improve.

The goal is not more graphics. The goal is a coherent, art-directed image that matches the concept's mood, palette, lighting and shape language, plus durable guidelines and tools so every future asset follows the same rules.

Do not redesign gameplay, change balance, remove systems, or break collisions. Keep the game playable.

## Prerequisites

- A runnable game with a real display/GPU for captures. Godot 4 and Three.js have notes and templates below; other engines need an equivalent capture tool. Verify with the engine itself (for example `godot --version`).
- Python 3 with Pillow and numpy: `python3 -m pip install Pillow numpy`; verify with `python3 -c "import PIL, numpy"`.
- A way to spawn a fresh reviewer that sees only images: a subagent, or a separate session when the tool has no subagents.
- The skill's resources, installed with it under `.claude/skills/art-direction-pass/` (other tools use their own skills directory): `assets/presets.json`, `assets/visual_capture.gd`, `scripts/compare.py`, `scripts/metrics.py`. See Templates for usage.

## Arguments

Read them from the invocation text. Defaults in brackets.

- `scope` [global,environment] — any of: `global`, `terrain`, `architecture`, `props`, `vegetation`, `characters`, `vfx`, `all`. `environment` = terrain + architecture + props + vegetation. Categories outside scope are frozen: do not modify their assets; only keep them readable through global lighting/post.
- `mode` [full] — `audit` (Phases 0–2 only, then stop), `full` (all phases), `codify` (Phase 4 only: extract guidelines/presets from the current state; requires an existing `docs/art/direction/`, otherwise run Phases 0–2 first, including Phase 1 when captures are possible).
- `concepts` [docs/art/reference/] — folder with concept images, optionally in subfolders per category.
- `max_iterations` [12], `min_iterations` [5].

If the scope or concept location is ambiguous and the user is present, ask once. Otherwise state the reading you took at the top of the iteration log and continue. Missing concepts are a stop condition, not an ambiguity.

## Git

The pass relies on a baseline, one recorded state per kept iteration and reverts of rejected ones. Follow the project's own Git rules: if its instructions require approval for commits, tags or branches, ask once before Phase 3 (`audit` needs no Git permission) for permission to commit iterations on the current (or a dedicated) branch. Never push, and never commit changes this pass did not make.

Without that permission, or when the working tree already has the user's own changes, use snapshots instead of commits. A snapshot is a tree object written through a temporary index; it creates no commit, ref or tag and leaves the project's index alone. `docs/art/` is excluded so reverts never touch the log, patches or captures:

```sh
snap() { idx=$(mktemp); GIT_INDEX_FILE=$idx git read-tree HEAD && GIT_INDEX_FILE=$idx git add -A -- . ':!docs/art' && GIT_INDEX_FILE=$idx git write-tree; rm -f "$idx"; }
```

- Baseline: `snap` before any change; record its id and `git rev-parse HEAD` in `docs/art/iterations/log.md`. The user's uncommitted and untracked files are part of it and never appear in iteration patches.
- Kept iteration: `snap` again, save `git diff --binary <last kept> <new>` as `docs/art/iterations/<NN>/change.patch`, record the new id as the last kept state.
- Rejected iteration: `snap` the current state as `<cur>`, run `git diff --binary <cur> <last kept> | git apply --binary` (this also deletes files the iteration added), then check that a fresh `snap` equals `<last kept>`.

Never build on a degraded result either way.

## Stop conditions

- Captures cannot be produced (no display/GPU, for example in a sandbox or CI) or stay nondeterministic after a reasonable fix attempt: deliver the `audit` outputs, report the blocker, and do not start Phase 3.
- No fresh blind reviewer can be spawned: same as above. Never review your own changes in place of the blind reviewer.
- No concept images at `concepts`: ask if the user is present; otherwise stop after Phase 0 notes and report it. Never derive the target from the game itself.
- The game no longer runs or existing tests fail after a change: revert that change before anything else.

## Phase 0 — Discover

1. Read the project's agent instructions (`AGENTS.md` or the tool's own instruction file), README and any existing `docs/art/`. If `docs/art/` exists, this is a follow-up pass: update the existing documents, never rewrite them from scratch, and append to `docs/art/CHANGELOG.md`.
2. Identify: engine and version, renderer, color space, target platform and FPS, gameplay camera (projection, pitch, distance, FOV), resolution, how to run the game, existing tests.
3. List the categories that actually exist in this game. Only create guideline files for those.
4. Record the baseline (see Git). With commit permission and a clean tree, tag the current commit `visual-baseline-<date>` (or the next free tag); otherwise take the baseline snapshot and create no tag.

## Phase 1 — Capture Harness

Subject to the stop conditions. Visual work without reproducible screenshots is guessing. Build or reuse a capture tool before any visual change.

Requirements:
- Named camera presets in `tools/visual/presets.json`: at least `gameplay_wide` (the real gameplay camera), one `gameplay_<area>` per distinct biome/area, and one close-up per in-scope category. Close-ups never replace gameplay-distance checks.
- Deterministic: fixed RNG seed applied before level generation, paused animations/particles, fixed time of day/weather.
- Settle frames before capture (shadows, TAA, GI, auto-exposure).
- Output to `docs/art/iterations/<NN>/<preset>.png` (`00` is the baseline) plus `perf.json` (average GPU and CPU render time per preset, measured with vsync off).
- Verify: two consecutive runs of the same build produce identical (or near-identical, mean abs diff < 1/255) images. Fix nondeterminism before Phase 3.

Prefer a capture method already described in the project's instructions; otherwise use the templates.

## Phase 2 — Forensics and Direction

Analyse the concepts and the current game separately, then compare.

### Direction documents

```
docs/art/
  direction/
    00-global.md          # applies to everything
    10-terrain.md
    20-architecture.md    # buildings, structures, walls, bridges
    30-props.md
    40-vegetation.md
    50-characters.md      # heroes, NPCs, enemies, mechs, vehicles, units
    60-vfx.md
  gap-report.md
  iterations/
  CHANGELOG.md
  reference/              # concepts, per category if available
```

Every statement must be an actionable constraint with numbers where possible. Bad: "richer, more polished". Good: "roofs overhang walls by 0.4–0.6 m; recessed openings are 2–3 value steps darker than the wall".

If a trait cannot be read confidently from the concept, write it under `Uncertain` instead of inventing it. The concepts may be AI-generated: they define mood, palette, lighting, value structure, shape language and detail density — not every individual detail. Never copy non-functional or physically implausible details.

**00-global.md** sections:
- Mood in one sentence, then the 5 traits that create it
- Palette: dominant / secondary / accent as hex, with value (0–100) and approximate share of screen
- Value structure: where the darkest and lightest values live; foreground/midground/background separation
- Lighting: key direction (azimuth/elevation), key color and intensity, fill/ambient color, shadow color, shadow softness, warm/cool relationship
- Atmosphere: fog color, density, height falloff, aerial perspective, sky
- Post: tone mapper, exposure, contrast, saturation, grading, bloom (only with purpose), AA, AO
- Camera and composition: projection, angle, framing, focal hierarchy
- Global material rules: roughness ranges, metallic usage, texel density (px/m), bevel width scale, weathering level
- Readability rules: what must always stand out at gameplay distance
- Uncertain

**Each category file** (10–60) uses the same template:
- Role in the scene (focal / supporting / background) and screen share
- Shape language: dominant forms, angular vs soft, exaggeration, bevel/chamfer width
- Proportions and scale with numbers (relative to player/character height)
- Detail hierarchy: macro / medium / micro — what goes where, density, quiet areas
- Materials: preset table — name, albedo hex, roughness, metallic, normal strength, texture scale
- Palette slice: which global colors this category may use
- Readability: value/hue separation from neighbours at gameplay distance
- Asset spec for NEW assets: triangle budget, texel density, pivot and scale conventions, naming, which material presets to use, LOD rules. Write it so an asset-generation pipeline (e.g. Blender scripts) can follow it mechanically.
- Do / Don't (short, concrete)
- Uncertain

Category-specific emphasis:
- terrain: macro value variation, tiling breakup at gameplay distance, blend transitions, contact with objects
- architecture: silhouette variety, roof/overhang thickness, recess depth, grounding, construction logic
- props: clustering, scale consistency, they support rather than compete
- vegetation: cluster shapes, color variation range, wind motion, density at gameplay camera
- characters: silhouette and value separation from environment, team/faction color rules, rigid vs skinned parts, emissive usage
- vfx: color and value budget relative to the scene, bloom budget, duration, readability of gameplay information

### Gap report

`docs/art/gap-report.md` — a prioritized table: Category | Target | Current | Root cause (geometry / material / texture / lighting / camera / color management / environment design / missing context / inconsistency) | Fix | Impact | Effort | Verification | Status.

Do not start with textures when lighting, values or composition are the real problem.

### Checkpoint

If the user is present: stop, show `00-global.md` and the top 10 gaps, wait for approval. A wrong reading of the concept poisons every iteration. If unattended, continue and note it in the log. In `audit` mode, stop here.

## Phase 3 — Iterate

Subject to the stop conditions.

### Priority order

Work top-down. Global, scene-wide fixes before per-asset fixes.

1. Color management, tone mapping, exposure
2. Key light, fill/ambient, shadows
3. Atmosphere and depth: fog, aerial perspective, sky, grading
4. Global palette and value structure
5. Shared material presets per category
6. Composition and environment design (set dressing, clustering, negative space)
7. Geometry: silhouettes and proportions, only where they clearly contradict the concept
8. Secondary detail and polish

### Loop

Each iteration:
1. Capture all presets.
2. Build comparison sheets with `compare.py sheet` and metrics with `metrics.py`.
3. Diagnose the 3–5 biggest remaining discrepancies; separate root causes from symptoms.
4. Change ONE group (lighting, or materials, or atmosphere…). For uncertain parameters, try 2–3 clearly different variants instead of tiny nudges.
5. Capture again and run the blind reviewer on every preset.
6. Keep or revert based on the evidence. Never build on a degraded result.
7. Record a kept iteration as `art(<NN>): <what changed> — reviewer <old>→<new>` (commit message, or the saved diff's heading). Append to `docs/art/iterations/log.md`: discrepancies addressed, changes, parameters, reviewer scores, remaining issues, frame time delta.

An iteration's gain is mean(after) − mean(before) over all criteria and presets, scored in the same review; a reverted iteration counts as 0. Stop after at least `min_iterations` when two consecutive iterations each gain < 0.5, or at `max_iterations`.

Never claim an improvement without an updated render. If capture fails, say so; do not pretend to verify.

### Blind reviewer

Every iteration, spawn a FRESH reviewer (subagent or separate session). For each preset, run `compare.py blind` into a temporary directory outside the project (`-o <tmp>/<NN>/<preset>`) with the mapping kept in the project (`--mapping docs/art/iterations/<NN>/blind/<preset>.mapping.json`). Each preset is shuffled separately, so A and B mean different things per preset. Copy the concept images for the in-scope categories (and the global ones) into `<tmp>/<NN>/concepts/`. Give the reviewer only absolute paths inside `<tmp>/<NN>/`, tell it to open only the listed files and never list directories or read anything else, and run it without project access where the tool allows. It never sees code, diffs, the log, the mappings or the project's capture folders.

To compare 2–3 variants of one change, review each variant against the last kept state and keep the one with the best gain among those the reviewer prefers.

For each preset it must:
1. Choose which of A/B is closer to the concept in overall mood and style, and why.
2. Score both 1–5 on: mood, lighting, palette, value/contrast, atmosphere/depth, materials, cohesion, focal readability. Add category-specific criteria for in-scope categories.
3. List the top 3 remaining discrepancies.

Keep a change only if the reviewer prefers it on `gameplay_wide` and on a majority of all presets. Metrics are supporting evidence; the reviewer and gameplay readability decide.

### Rules for effects

Every new effect needs: the discrepancy it addresses, why this technique, its parameters, its cost, how it was verified. No universal bloom, saturation boosts, vignette or fog used to hide weak models or materials. No uncontrolled procedural noise, random decoration, arbitrary lights or excessive particles. Do not raise polygon counts without a visible benefit.

## Phase 4 — Codify

The result must survive the next asset. Turn what worked into data and rules.

- **Graphics profile**: one central place for all look parameters (Godot: a `GraphicsProfile` Resource `.tres` applied by a script to WorldEnvironment, lights and post; Three.js: a single `graphics-profile.json/ts`). No magic numbers scattered through the code.
- **Material presets library**: one file per preset, grouped by category (Godot: `res://art/materials/<category>/<preset>.tres`). Assets reference presets instead of ad-hoc materials.
- **Direction docs**: update every category file with the final numbers that actually shipped (light angles, hex values, roughness ranges, budgets). Mark what was verified vs still uncertain.
- **Asset checklist**: a short checklist per category at the end of each file, for whoever (human or agent) makes the next asset.
- Optional **asset lint** script: flags meshes using non-preset materials, wrong scale, triangle budget overruns, texel density outliers.

Codify refactors must not change the image: capture every preset before and after with the Phase 1 harness and require a mean abs diff < 1/255. If captures are impossible, say the refactor is visually unverified.

In `codify` mode, do only this phase from the current state.

## Phase 5 — Final review

Write `docs/art/iterations/final.md`: before/after sheets for every preset, top improvements, remaining discrepancies and why they were not resolved, next highest-impact steps, frame time before/after, confirmation that the game still runs and existing tests pass. Do not declare the target achieved unless the screenshots support it.

## Constraints

- Work in the existing stack; no new frameworks or heavy dependencies (Pillow and numpy for tools are fine).
- Respect performance: measure frame time per preset every iteration; document any trade-off over 10%.
- Do not distort the gameplay camera to win a pixel-level match.
- Prefer one global fix over many local patches, but keep meaningful variation where the concept has it.

## Engine notes

**Godot 4**
- `--headless` does not render. Capture with a real display/GPU.
- Look levers: WorldEnvironment (tonemap: Filmic/ACES/AgX where available, exposure, white; SSAO, SSIL, SDFGI or baked lightmaps/VoxelGI; volumetric fog, depth/height fog; glow; adjustments + color correction LUT), DirectionalLight3D (angle, color, energy, shadow blur, PSSM splits, bias), ReflectionProbe, decals, StandardMaterial3D roughness/metallic/normal.
- Check the renderer (Forward+/Mobile/Compatibility): many effects only exist in Forward+.

**Three.js**
- Capture via Playwright in headed mode; renderer with `preserveDrawingBuffer: true`, then `canvas.toDataURL()`.
- Look levers: `outputColorSpace`, `toneMapping` (ACES/AgX/Neutral) + `toneMappingExposure`, PMREM environment, shadow map type and radius, postprocessing (SSAO/GTAO, bloom, color grading), fog/FogExp2.

## Templates

Copy `assets/` templates into `tools/visual/` and adapt them to the project. Invoke the `scripts/` tools by path from the project root, so relative outputs land in the project.

- `assets/presets.json` — scene, seed, settle frames and camera presets (`name`, `pos`, `target`, `fov`; `ortho: true` with `size` for orthographic cameras).
- `assets/visual_capture.gd` — Godot 4 autoload `VisualCapture`. Run:
  `godot --path . --resolution 1920x1080 -- --visual-capture=res://tools/visual/presets.json --visual-out=/abs/path/docs/art/iterations/01`.
  If the game's camera controller fights `make_current()`, disable it for capture. If particles keep moving while paused, set their `speed_scale` to 0 during capture.
- `scripts/compare.py` — `compare.py sheet REF BEFORE [AFTER] -o sheet.png`; `compare.py blind BEFORE AFTER -o <tmp>/<NN>/<preset> --mapping docs/art/iterations/<NN>/blind/<preset>.mapping.json` writes `A.png`/`B.png` and refuses a mapping inside the reviewer folder.
- `scripts/metrics.py` — `metrics.py IMG [IMG...] -o metrics.json`: luminance percentiles (p5/p50/p95), mean saturation and a 6-color palette with screen shares. Compare reference vs current: large gaps point to tone mapping/exposure (luminance), grading (saturation) or materials/lighting color (palette).

Tests of the tools themselves: `python3 -B -m unittest discover -s .claude/skills/art-direction-pass/scripts` (skipped without Pillow and numpy).

## Output

- `audit`: `tools/visual/` with the capture harness (and its autoload registration), `docs/art/iterations/00/` (baseline captures, `perf.json`), `docs/art/iterations/log.md`, `docs/art/direction/00-global.md`, category files for in-scope categories, `docs/art/gap-report.md`; report the top 10 gaps and any stop condition hit. Without captures, mark the gap report's Current column as read from code, unverified.
- `full`: the above plus `docs/art/iterations/<NN>/`, the codified profile and presets, and `final.md`; report the reviewer score trajectory, frame time before/after and the remaining discrepancies.
- `codify`: the graphics profile, material presets and updated direction docs, plus whatever Phases 0–2 created when `direction/` was missing; report the files changed and whether the image was verified unchanged.
