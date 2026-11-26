---
name: concept-asset-builder
description: Build ONE game object (prop, machine, street furniture, building part) from a concept or asset sheet to the highest visual fidelity, in Blender and/or Three.js (Godot via GLB), in the shared style of its scene. Measured spec from the concept's pixels, generated textures, a numeric wear description per part and side, a builder agent plus a context-free cross-model reviewer with a weighted rubric, an owner checkpoint that feeds a scene style file, optional engine transfer. Use it whenever someone wants a single object to look like its concept art ("make this post box / vending machine / lamp like the concept", "match the asset sheet", "why does my model look worse than the concept"), when concept-scene-builder reaches a hero asset, or when a scene is built object by object as a conveyor. Not for whole-scene layout (concept-scene-builder), global lighting/post (art-direction-pass) or rigged characters.
---

# Concept Asset Builder

You turn a concept of ONE object into a 3D asset that a person comparing them side by side accepts as "the same thing", and that sits in its scene next to the other objects in one style. The method comes from real runs (a Japanese post box as the pilot object of a shop scene, then a vending machine built through the conveyor); see `references/field-lessons.md` for what failed and why.

Why this exists: an LLM writing geometry "by eye" plateaus fast. What actually moves the result is (1) measuring instead of guessing, (2) a written, numeric description of the target that a builder and a reviewer share, (3) an independent reviewer that sees only the reference, the render, the description and its own previous review, and (4) the owner's remarks captured once in a scene style file instead of being repeated for every object. Surface wear (chips, drips, edge wear) is the hardest layer and the usual ceiling; plan an owner checkpoint for it.

## Prerequisites

- Python 3 with Pillow, numpy and scipy: `python3 -m pip install Pillow numpy scipy`; verify with `python3 -c "import PIL, numpy, scipy"`.
- Blender 4.2 or later for the Blender pipeline and for baking. Find it as `blender` on PATH, the `BLENDER` environment variable or the standard install location (macOS: `/Applications/Blender.app/Contents/MacOS/Blender`) and verify with `--version`.
- For the Three.js pipeline: Node 20+, `three` and `vite` in the workspace (or a parent folder), Playwright with Chromium for `capture.mjs`.
- Optional: the Codex CLI with image input for the independent reviewer and for generated sheets/textures (`codex --version`). Without it, the reviewer runs as a fresh subagent with the same inputs (Phase 5), and sheets/textures come from the user or another image tool.
- Optional: Godot 4 for engine transfer (renders only with a real display/GPU).
- The skill's resources, installed with it under `.claude/skills/concept-asset-builder/` (other tools use their own skills directory): `scripts/` (copied into each object workspace by `scripts/init_workspace.sh`), `references/`, `assets/templates/`. Run `init_workspace.sh` by its path; everything else runs from the workspace.

## Git

Follow the project's own Git rules. This skill works in its own object workspace and creates no commits, tags or branches by itself; if the project wants the workspace or the exported asset committed, ask once and commit only files this run created. Never push.

## Stop conditions

- No concept and no scene image to generate a sheet from: ask if the user is present; otherwise stop and report it. Never invent the target.
- No real height or scale reference for the object and the user is not present: state the assumption in `spec/object.json` (`_note`) and in the report, and continue.
- Renders cannot be produced (no Blender, no browser for Three.js, no GPU): deliver the reference, spec, wear description and rubric, report the blocker, and do not start Phase 4.
- The reviewer tool is missing and no subagents are available: review against the description yourself in a fresh pass with only the inputs, and say in the report that the review was not independent.

## 0. Inputs

Read from the invocation; defaults in brackets.
- `concept` — an asset sheet with several views (3/4, front, back, left, right, a detail) on a plain background. If there is only a scene image or a crop, generate the sheet first (Phase 1.2).
- `height_m` — real height of the object (a scale reference: door 2.0–2.1 m, post box ~1.35 m, vending machine ~1.8 m). Ask if nothing in the concept fixes it.
- `engines` [blender] — `blender`, `threejs`, or both (one builder per engine). Godot/other engines get the Blender result through a baked GLB (Phase 7).
- `scene_style` — the scene's style file (`style/<scene>_style.md`). Absent → this is the scene's PILOT object: you will create the file at the owner checkpoint.
- `style_library` — code of already approved objects of the same scene (their wear functions). Absent → start from `references/examples/`.
- `max_review_rounds` [3], `target_score` [8.5].

## 1. Workspace and reference

1. `.claude/skills/concept-asset-builder/scripts/init_workspace.sh <dir> <concept.png> [scene_style.md]` creates the layout below and copies the tools into `<dir>/tools`, the studios into `<dir>/blender` and `<dir>/threejs`. Work from `<dir>`.
   ```
   reference/concept.png, boxes.json, crops/{3q,front,back,left,right,detail}.png, zones.json
   spec/object.json            measured geometry, palette, cameras (Phase 2)
   brief/wear_description.md   numeric target (Phase 3); scene_style.md; rubric.json; agent_brief.md
   blender/ threejs/           studio (frozen) + the builder's code
   out/<pipeline>/<view>.png   renders; reviews/; reports/; textures/
   ```
2. **No sheet yet?** Generate one with Codex image generation (`codex exec -m gpt-6.2-sol -c model_reasoning_effort=high -i <scene crop> -i <an approved sheet of the same scene>`, prompt via stdin). Ask for: the same layout and rendering style as the approved sheet, 5 labelled views at the same scale and camera height, a detail panel, palette and proportions, neutral soft studio light (not the scene's mood light), and weathering in the scene's language (name it: chips to primer with ragged edges at edges and corners, short rust drips under seams, grime only at the bottom). Look at the result before using it; regenerate if views disagree or are cropped.
3. Cut the views: write `reference/boxes.json` ({view: [x0, y0, x1, y1]} in sheet pixels, include the whole object and a margin, exclude labels), run `python3 tools/crop.py`, LOOK at every crop.
4. View conventions (used by every studio): azimuth 0 = front (+Z), positive toward +X; `left` = −90 (the front edge appears on the RIGHT of the image), `right` = +90, `3q` = the sheet's 3/4 (estimate the azimuth from the visible front/side width ratio: tan(az) ≈ (W/D)·(side px/front px)). Elevation: 8–15° (top surfaces barely visible); all views share one elevation unless the sheet clearly differs.

## 2. Spec from pixels (geometry is measured, never eyeballed)

`python3 tools/measure_silhouette.py front --height <h>` (and `left`, `back`) prints mm/px, the width profile by height and the largest dark/bright components with their positions in metres. LOOK at the crop and name each component (opening, panel, window, button). Write `spec/object.json`:
- dimensions of the body and every visible part (metres; Y up, front +Z, ground y=0, x from the centre), counts (facets, shelves, slats, screws), edge radii;
- palette sampled from the concept (median of each paint zone, not your words);
- `cameras`: `fov_deg` 18, `elevation_deg`, `views` azimuths, `image` [560, 1100], `fill` 0.955 (object fills 95.5% of the image height, like the crops), `target_y`; `palette.background` = the sheet background.

Treat the spec as a draft: a contact shadow inside the silhouette shifts heights by a few cm, top surfaces add height, AI sheets disagree between views. Builders must log deviations they find (Phase 4) instead of silently following a wrong number.

## 3. Wear description (the shared numeric target)

This is the step that replaced most of the owner's corrections. Do it once per object, before any building.
1. **Calibrate the masks.** Edit `reference/zones.json` (template: `assets/templates/zones.json`, filled example `zones_example_vending.json`): horizontal `bands` in metres over the whole silhouette (every view) and `front_rects` for key parts; chip rule (`dL`, `min_L`, `max_C`, `window_m`; for light paint where chips differ by hue: `mode: "hue"`), rust rule (`mode: "dark"` for red/orange paint, `"hue"` with an orange-brown hue range for other colours), grime hue range, `exclude_emissive` for glowing windows. Run `python3 tools/wear_stats.py`, overlay the masks on the crops (chips, rust, grime in different colours) and LOOK. Expect 3–4 iterations; never trust a mask you have not overlaid. Typical traps: chips larger than the paint window vanish (use a wide chip window), light paint makes chips "not lighter", bright paint or the background read as a glowing window, louvres and highlights read as chips.
2. **Write `brief/wear_description.md`** from the numbers AND your eyes on 2x crops (example: `assets/templates/wear_description_example.md`):
   - the object in one paragraph (materials, paint zones, edge radii);
   - a table per zone: chip % of area, rust %, grime %, character (where, which sizes);
   - per part and per side: count and size classes of chips (small < 2 cm, medium 2–5, large ≥ 5 cm, with ranges), where they sit (edges vs faces), drip sources and lengths, edge-wear strength, special notes ("the door: drips matter more than wear", "back is not empty: 3–5 large flakes");
   - the measurement caveats (what the masks over/under-count on this object);
   - a short "do not" list.
3. **Rubric** `brief/rubric.json` (template `assets/templates/rubric.json`): keep the generic criteria (shape, paint, chips, edge_wear, drips, grime, style), replace `parts_*` with the object's key parts, weights sum to 1. The reviewer scores each 0–10; the script computes the weighted total, so scores are comparable between rounds.

## 4. Build

Prefer one fresh builder agent per engine (same model as you, high effort), working in parallel on separate files, with `assets/templates/agent_brief.md` filled in. A fresh agent with a written brief tests the method: if it fails, the brief or the description is missing something. Build yourself only for a single small object.

What every builder must know (put it in the brief):
- **Frozen studio**: `blender/studio.py` (camera-relative 3-light rig scaled to the object height, Standard view transform, exposure −0.3, shadow catcher) and `threejs/studio.js` + `threejs/index.html` (same convention; the model module exports `buildModel(spec)`). All objects of a scene are lit identically; never tune light to hide a material problem.
- **Commands**: Blender build `Blender -b --factory-startup --python blender/build_object.py` (ends with `studio.setup(SPEC); studio.save(ROOT, "object")`), render `Blender -b --factory-startup blender/object.blend --python blender/render_views.py -- --samples 32` (96 for finals); Three.js: a vite server rooted at the workspace, `node tools/capture.mjs threejs --base http://localhost:<port>`.
- **Geometry rules**: no sharp edges anywhere (real rounded geometry with smooth normals, 2–12 mm by part size); parts never intersect or float; counts and proportions from the spec.
- **Textures**: optional, via `tools/gen_texture.sh <out> <WxH> <x|xy|none> "<description>"` (Codex image generation, concept attached). A generated texture is only the paint base: clean out baked chips, moss and stains (hue/lightness filter) so wear comes only from the procedural layer tied to geometry; discard a texture with 20%+ "chips".
- **Wear language**: `references/wear-language.md` (chips as flakes, edges first, drip clusters with bell-curve lengths, grime only low, dull marks) with implementations in `references/examples/` and in the scene's style library. Copy functions; keep the scene's language.
- **Self-check before any review**: 5-view sheets (`tools/sheet.py`), 2x close-ups of every part, `python3 tools/wear_stats.py out/<pipeline>` against `out/wear_stats_concept.json`, `python3 tools/metrics.py <pipeline>` (silhouette IoU ≥ 0.9 per view, zone ΔE).
- **Decisions log** `reviews/<pipeline>_decisions.md`: what was done and why, deliberate deviations from the spec or description. The reviewer reads it.

## 5. Review loop

`tools/codex_review.sh <pipeline> <round>` (rounds 1..max_review_rounds; 3–10 minutes; run in the background and wait). The reviewer is a different model (Codex gpt-6.2-sol, high, read-only sandbox) with no context but: concept|render sheets per view, 2x close-ups, the description, the scene style, the rubric, the measurements of both, its own previous review and the builder's decisions log. It must keep its earlier requirements unless it explains why, and report fixed/improved/open for its previous top list. Output: `reviews/<pipeline>_r<n>.md` and `.json` with the weighted total.

- Stop early at `target_score`; otherwise apply the top fixes and run the next round. After the last round, only obvious small fixes.
- Then run one more review of the FINAL renders (round `max+1`) so the reported score matches what is delivered.
- If Codex is unavailable, run the same prompt through a fresh subagent that receives only those inputs. Never let the builder review itself.
- Expect: shape/paint/parts reach 8–9 quickly; chips and drips plateau around 6. That plateau is the owner checkpoint's job (Phase 6), not another review round.

## 6. Owner checkpoint and the scene style file

For the PILOT object of a scene (no `scene_style` yet), and for any object whose wear stays below the target, show the owner: concept | result per view, 2x close-ups of the key parts and, if the scene has approved objects, a line-up with them at true relative scale. Ask what differs and what matters.

Record every remark that generalises beyond this object into the scene style file (`assets/templates/scene_style_example.md` is the pilot's file from a real run): numbered rules under Geometry / Wear / Textures / Engines, each with the reason in a few words ("chips are flakes, not paint spots: ragged edge, satellite flecks, rim"). Object-specific remarks go to the object's description. The style file travels with every later object of the scene (as brief input and reviewer input); that is how the second object avoided every complaint about the first one without the owner.

## 7. Engine transfer (optional)

Blender is the reference renderer; other engines get the asset as a baked GLB:
- `Blender -b blender/object.blend --python blender/bake_export.py -- --samples 96` bakes base colour (with procedural wear), AO (multiplied into the colour), roughness and normal per part into one atlas and joins the parts only AFTER baking (joined, the edge masks read the joints between parts as edges and bake light outlines).
- In the target engine turn runtime AO off (it is baked), and calibrate to the Blender render with light intensity and exposure, not with material colour (a colour multiplier tints chips and marks). `tools/compare_to.py <pipeline> blender` prints zone lightness/chroma deltas; aim for |ΔL| ≤ 5.
- Keep the page background identical: tone mapping also darkens a coloured background (three.js: scale the background colour to compensate; Godot: render with a transparent background and composite, `tools/composite_godot.py`). Godot capture: `scripts/godot/` (copy `project.godot` and `capture.gd` next to `object.glb`, `godot --headless --path . --import`, then `godot --path . --script capture.gd`; Godot does not render headless).

## 8. Deliverables

- `out/<pipeline>/<view>.png` for every engine, a sheet `concept | result` per view, close-ups of key parts, and a line-up with the scene's approved objects.
- `reports/<pipeline>.md` per builder: plan, per-round changes and scores (per criterion and weighted), final per-criterion table, deviations, time, what got in the way.
- Your summary to the owner: scores per round, what matches, what does not, which remarks you propose for the scene style file.
- Never report a match without renders you looked at; never call wear "done" without a close-up.

## References

- `references/wear-language.md` — the shared wear model and how to implement it in Blender and Three.js. Read before writing any wear code.
- `references/field-lessons.md` — what went wrong in real runs (measurement, reviewers, textures, light, engines) and the fixes. Read before Phase 3 and before the first review.
- `references/examples/` — complete implementations from the pilot scene: `postbox_blender.py` (geometry helpers, `weathered_paint`, `drips`, edge wear), `postbox_wear_three.js`, `vending_materials_blender.py`, `vending_wear_three.js`. Large files; read the functions you need.
- `assets/templates/` — `agent_brief.md`, `rubric.json` (+ `rubric_example_vending.json`), `zones.json` (+ `zones_example_vending.json`), `wear_description_example.md`, `scene_style_example.md`.
