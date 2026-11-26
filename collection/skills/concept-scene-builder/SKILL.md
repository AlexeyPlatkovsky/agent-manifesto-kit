---
name: concept-scene-builder
description: Build a game environment scene (terrain, water, roads, vegetation, rocks, buildings, props, lighting; no units or vehicles) that matches a concept image or screenshot as closely as possible in style and layout, from a reusable asset kit and data-driven layout. Decomposes the scene into objects and builds the hero/mid objects through an object conveyor (a pilot object approved by the owner, a scene style file, then the rest in parallel via concept-asset-builder), then assembles the scene and runs the look pass. Any genre, grid or free-form. Godot or Three.js + Blender. Use when a game needs its environment rebuilt from a concept image or screenshot.
---

# Concept Scene Builder

You build an environment scene that matches a concept image in style AND layout, using a reusable, data-driven asset kit. The concept can be anything: a tiled board, a grid map, an isometric scene, a top-down map, a third-person or in-game screenshot. No genre or game is assumed. The output is not one pretty scene but:
1. a kit of parametric assets (engine-procedural + Blender scripts),
2. a layout format and a scene builder that turns layout data into a scene,
3. a "golden scene" — the concept layout rebuilt as data — used as the comparison fixture,
4. style documents shared with the `art-direction-pass` skill.

Units, mechs, characters and vehicles visible in the concept are NOT built. Ignore them (optionally record their positions as `spawn_hints`).

## Prerequisites

- Python 3 with Pillow and numpy: `python3 -m pip install Pillow numpy`; verify with `python3 -c "import PIL, numpy"`.
- Godot 4 or Three.js (Node, Playwright for captures), and Blender 4.2 or later for kit assets. Find Blender as `blender` on PATH, the `BLENDER` environment variable or the standard install location (macOS: `/Applications/Blender.app/Contents/MacOS/Blender`) and verify with `--version`; only when none works, build everything in-engine at lower fidelity.
- A real display/GPU for captures (`--headless` Godot does not render).
- Optional: the `concept-asset-builder` skill for the object conveyor (5.0): one object to concept fidelity with an independent review loop and a scene style file. Without it, `asset` entries are built as Blender assets.
- Optional: the `art-direction-pass` skill. It shares the `docs/art/` format, provides `compare.py`, the capture harness and the look pass (Phase 6). Without it, use the fallbacks named in each phase.
- The skill's resources, installed with it under `.claude/skills/concept-scene-builder/` (other tools use their own skills directory): `scripts/grid_overlay.py`, `scripts/crop.py`, `scripts/blend.py`, `references/field-lessons.md`. Invoke the scripts by path from the project root, so relative outputs land in the project.

## Git

Follow the project's own Git rules. The workflow below names commits (a baseline tag, one commit per finished asset family and per scene iteration): if the project's instructions require approval for commits or tags, ask once at the start. Without permission, or with the user's own uncommitted changes in the tree, create no commits or tags and never commit changes this run did not make; use snapshots instead. A snapshot is a tree object written through a temporary index; it creates no commit, ref or tag and leaves the project's index alone. `docs/art/` is excluded so reverts never touch the records:

```sh
snap() { idx=$(mktemp); GIT_INDEX_FILE=$idx git read-tree HEAD && GIT_INDEX_FILE=$idx git add -A -- . ':!docs/art' && GIT_INDEX_FILE=$idx git write-tree; rm -f "$idx"; }
```

- Baseline: `snap` before any change; record its id and `git rev-parse HEAD` in `docs/art/kit.md`. The user's uncommitted and untracked files are part of it.
- Finished step: `snap` again and record the id with the files the step created or changed in `kit.md`.
- Revert: `snap` the current state as `<cur>`, run `git diff --binary <cur> <last kept> | git apply --binary` (this also deletes files the step added), then check that a fresh `snap` equals `<last kept>`. Never use tree-wide `checkout`, `reset`, `clean` or `stash`.

Never push.

## Stop conditions

- No `scene` image: ask if the user is present; otherwise stop and report it. Never invent the target.
- Captures cannot be produced (no display/GPU, e.g. a sandbox or CI): deliver the Phase 0–2 outputs (style docs, `kit.json`/`kit.md`, layout JSON and overlay), report the blocker, and do not start Phase 4.
- The game no longer runs or existing tests fail after a change: revert that change before anything else.

---

## 0. Inputs and arguments

Read from the invocation text. Defaults in brackets.

- `scene` — concept image(s) or screenshot(s) of the assembled scene (required): any camera — top-down, isometric, perspective, third-person.
- `kit` — kit sheet(s) with individual assets (optional but strongly preferred).
- `engine` [auto] — `godot` or `threejs`. Detect from the project; if there is no project, ask once if the user is present; if unattended, create a minimal Godot 4 project.
- `space` [auto] — `hex`, `square` (the concept has a visible game grid) or `free` (no grid: positions in metres). Detect from the concept; when in doubt, use `free`.
- `layout_fidelity` [close] — `close`: rebuild the concept layout as precisely as the camera allows (cell by cell on grids, object by object in metres otherwise); `style`: same composition and kit, layout may differ.
- `max_asset_iterations` [4] per asset; scene look tuning is delegated (Phase 6).

Concepts are often AI-generated. They are the source of truth for style, palette, lighting, materials, proportions and layout intent — not for geometric consistency. Expect: buildings that overflow their cell, roads and rivers that ignore the grid, inconsistent scale between objects, more than one vanishing point, details that change between the scene and the kit sheet. Resolve each contradiction into an explicit rule (section 3.3) instead of copying it or silently ignoring it.

---

## 1. Phase 0 — Discover

1. Read the project's agent instructions (`AGENTS.md` or the tool's own instruction file) and README. Detect engine, renderer, color space, existing map/grid format, existing `docs/art/`.
2. If the project already has a grid/map format, write an adapter from this skill's layout JSON to it instead of replacing it.
3. Check Blender (see Prerequisites for where to find it). Assets are generated headless: `blender -b --python tools/blender/kit/<id>.py -- --out <path>.glb --seed N`. If Blender is missing, say so and build everything in-engine (lower fidelity for trees/rocks/buildings); the build-time placement checks of 5.3 then apply to the in-engine builders.
4. If `docs/art/` exists (from `art-direction-pass` or a previous run), extend it; never overwrite it.
5. Record the baseline within the Git rules above: tag the current commit `scene-baseline-<date>` when tags are allowed; otherwise note `git rev-parse HEAD` and the uncommitted file list in `docs/art/kit.md`.

## 2. Phase 1 — Style deconstruction

Write or extend `docs/art/direction/00-global.md` (the `art-direction-pass` format: mood and its 5 traits, palette hex + value + screen share, value structure, lighting, atmosphere, post, camera, global material rules, readability, Uncertain).

Then add a section **Signature traits**: the 5–8 traits that make this concept recognisable, ranked by impact. Each trait gets: description, technique, owner (asset / shader / lighting / post / camera), verification. Derive them from THIS concept; the table below is only an example (a tabletop-diorama concept):

| Trait | Technique | Owner |
|---|---|---|
| Miniature look | shallow depth of field / tilt-shift focused on board centre | post + camera |
| Tiles as physical objects | hex prism, beveled top edge, earth/cork side band ~8–10% of width | asset |
| Flocked grass | high-frequency noise albedo + instanced tufts, olive→straw variation | shader + scatter |
| Foam-clump trees | trunk + clusters of displaced blobs, conifers as stacked noisy cones | Blender |
| Resin water | glossy, translucent, visible bed | shader |
| Soft studio light | large soft key, soft shadows, dark table backdrop | lighting |

Every signature trait must be implemented and verified before the scene counts as done.

## 3. Phase 2 — Kit and layout extraction

### 3.1 Kit inventory

`docs/art/kit.json` (+ human-readable `docs/art/kit.md`). One entry per asset:

```json
{
  "id": "tile_grass",
  "category": "terrain",
  "build": "engine",
  "reference": "docs/art/reference/kit/tile_grass.png",
  "dimensions": {"relative_to": "tile", "width": 1.0, "height": 0.1},
  "variants": 4,
  "materials": ["flock_grass", "tile_side_earth"],
  "tri_budget": 2000,
  "screen_share": "high",
  "notes": ""
}
```

- `build`: `engine` (tiles or terrain meshes, ground surfaces, grass/scatter, water, road and river surfaces, simple cliffs), `blender` (trees, rocks, buildings, ruins, bridges, complex props), `shader` (surface-only effects), `asset` (an object the viewer looks at closely — street furniture, machines, signs, shop fronts, hero props: built through the object conveyor, 5.0, with the `concept-asset-builder` skill).
- Large objects (a shop, a station, a house with a porch) are decomposed: a parent entry with `"parts": ["shop_building", "shop_awning", "shop_shelves", "shop_counter", ...]` and an `assembly` block (part ids with positions/rotations in the parent's metres). Every part is its own kit entry (usually `asset`) and gets its own sheet; decompose recursively until each part is one object a sheet can describe in 5 views.
- `dimensions`: relative to the tile for grid concepts, in metres for free-form concepts.
- `category`: terrain / architecture / props / vegetation / vfx — same categories as `art-direction-pass`.
- Derive the list from the kit sheet AND the scene concept: anything visible in the scene must exist in the kit.
- Cut references with `crop.py` (look at the sheet, write `boxes.json`, run, check the crops). If there is no kit sheet, crop from the scene concept.

### 3.2 Layout extraction

Every scene has a ground plane. Map the concept's ground onto it first, then read the layout from that mapping. `grid_overlay.py` does both jobs.

**Grid concepts (`hex` / `square`):**
1. Estimate grid type, orientation (pointy/flat), columns, rows and the image pixels of the board's four corners.
2. Run `grid_overlay.py` and LOOK at the overlay. Adjust corners/cols/rows until cell outlines match the concept's cells. Raised tiles look shifted, the board is treated as a plane.
3. Read the concept cell by cell and fill the layout JSON.

**Free-form concepts (`free`):**
1. Find a scale reference: objects of known size (door ≈ 2.1 m, road lane ≈ 3.5 m, car ≈ 4.5 m, person ≈ 1.8 m, storey ≈ 3 m). Record which ones you used.
2. Pick four ground points that form a rectangle in the world (field corners, road edges, a building footprint, a plaza). Estimate its size in metres.
3. Run `grid_overlay.py --grid square --cell-m <size>` as a MEASUREMENT grid: each label is the metre coordinate of its cell's centre. Adjust until the grid lies convincingly on the ground (parallel to roads, square on building footprints).
4. Read positions, sizes and rotations of everything on the ground in metres. Elevated parts (hills, roofs, plateaus) are measured at their base.
5. In perspective or third-person views, measure only the ground region where the grid is reliable. Treat the horizon, skyline and distant hills as `backdrop` elements with a direction and rough distance, not as precisely placed objects.

Save the final overlay next to the layout; it is the evidence for every placement.

Layout format `docs/art/layout/<scene>.json`. The `space` block decides how positions are written.

Grid example:

```json
{
  "space": {"type": "hex", "orientation": "pointy", "coords": "axial", "cell_size_m": 2.0},
  "cells": [
    {"q": 0, "r": 0, "terrain": "grass", "height": 0, "features": ["rock_small"], "seed": 11}
  ],
  "paths": [
    {"type": "road", "cells": [[4, 7], [4, 6], [5, 5]], "style": "spline_through_centres"},
    {"type": "river", "cells": [[-1, 3], [0, 3], [1, 4]], "width": 0.45}
  ],
  "structures": [
    {"kit": "factory_a", "anchor": [5, 0], "footprint": [[5, 0], [6, 0]], "rotation_deg": 0}
  ],
  "scatter": [
    {"kit": ["tree_conifer", "tree_broadleaf"], "cells": [[10, 1], [11, 1]], "density": 0.9, "seed": 5}
  ],
  "camera": {"preset": "concept_view"},
  "spawn_hints": [{"cell": [3, 1], "note": "unit in concept"}],
  "notes": ["factory_a overflows one hex in the concept -> 2-hex footprint"]
}
```

Free-form example (metres, x right, y away from camera, height up):

```json
{
  "space": {"type": "free", "units": "m", "extent": [0, 0, 120, 80], "scale_refs": ["road lane 3.5 m", "door 2.1 m"]},
  "terrain": {
    "heights": [{"at": [30, 20], "h": 4.0, "radius": 12, "profile": "plateau"}],
    "regions": [{"material": "dry_grass", "polygon": [[0, 0], [40, 0], [40, 25], [0, 30]]}]
  },
  "paths": [
    {"type": "road", "points": [[0, 60], [50, 45], [120, 40]], "width": 6.0},
    {"type": "river", "points": [[0, 30], [60, 35], [120, 28]], "width": 4.0}
  ],
  "objects": [{"kit": "factory_a", "pos": [62, 18], "rot_deg": 15, "scale": 1.0}],
  "scatter": [{"kit": ["tree_conifer"], "polygon": [[90, 0], [120, 0], [120, 30]], "density_per_100m2": 2.0, "seed": 5}],
  "backdrop": [{"kit": "hills_far", "direction_deg": 0, "distance_m": 400}],
  "camera": {"preset": "concept_view"},
  "spawn_hints": [],
  "notes": []
}
```

Square grids use `x, y` instead of `q, r`. If the project already has its own map format, keep this JSON as the extraction result and write an adapter.

### 3.3 Contradiction rules

Record every resolution in `layout.notes` and in `kit.md`:
- Building larger than a cell → multi-cell footprint, or an allowed overhang (state the max, e.g. ≤ 15% of a cell). Never scale the grid to fit one building.
- Road or river not aligned with the grid → path through cell centres, smoothed with a spline, keeping the concept's visual direction as closely as the grid allows.
- Inconsistent cell sizes → one cell size.
- Objects at inconsistent scales (free-form) → normalise to the scale references; note the objects that were resized.
- Several vanishing points or a distorted ground → pick the dominant ground plane, accept small placement errors elsewhere.
- Scene and kit sheet disagree on an asset → the scene wins for proportions in context, the kit sheet wins for detail and materials.
- The user overrides the concept ("the concept is wrong here") → record it as a rule like the ones above, so no later pass reverts it.

### 3.4 Checkpoint

If the user is present: show signature traits, the kit list, the overlay image, the scale references (free-form) and the contradiction rules; wait for approval. If unattended, continue and note it.

## 4. Phase 3 — Foundations

1. **Scene builder** — reads layout JSON + kit.json and builds the scene: tiles or a terrain mesh, surface regions, paths, objects, scatter, backdrop. No hand-placed objects: everything comes from data, so the same code builds any future map or level.
   - Godot: `SceneBuilder` node with an `@tool` script (rebuild in editor and at runtime).
   - Three.js: `buildScene(layout, kit)` module returning a `Group`.
   - Instancing for repeated meshes (MultiMeshInstance3D / InstancedMesh), shared materials, deterministic seeds.
2. **Material presets library** — one preset per material in kit.json (`res://art/materials/<category>/` in Godot, a `materials.ts/json` registry in Three.js).
3. **Capture harness** — reuse the one from `art-direction-pass` if present (same `tools/visual/`). Otherwise build one: named camera presets in `tools/visual/presets.json`, a fixed RNG seed applied before generation, paused animation and particles, settle frames before each capture, a PNG plus frame time per preset, and two identical runs (mean abs diff < 1/255) before relying on it. Presets:
   - `concept_view` — camera matched to the scene concept,
   - `kit_<id>` — each asset alone on a neutral background in the kit sheet's angle,
   - `gameplay_wide` — the real gameplay camera, if the game has one.
4. **Camera match** — render `concept_view` with debug cell outlines (or the measurement grid for free-form), overlay it on the concept with `blend.py`, adjust position/pitch/FOV until the grids coincide. Do this before any style work: a wrong camera makes every comparison misleading.

## 5. Phase 4 — Build the kit

### 5.0 Object conveyor (`build: asset`)

Objects the viewer looks at closely are built one by one to concept fidelity with the `concept-asset-builder` skill, in one shared style. The conveyor gets early owner feedback on ONE object and then runs the rest without the owner. Without that skill, build `asset` entries as Blender assets (5.3) and keep the pilot and style-file steps.
1. **Sheets.** Each `asset` entry needs an asset sheet (5 views + detail on a plain background). Cut it from the kit sheet if there is one; otherwise generate it from the scene crop in the layout and rendering style of an approved sheet (concept-asset-builder 1.2). Keep all sheets of a scene visually consistent (same background, light, weathering language).
2. **Pilot.** Pick one object of medium complexity with a high screen share and the scene's typical materials (not the simplest, not the hardest). Build it with concept-asset-builder in pilot mode. Show it to the owner (concept | result per view, close-ups); record every remark that generalises into `docs/art/style/<scene>_style.md` (numbered rules with reasons). Iterate until the owner accepts the pilot. Do not start other assets before this: every remark on the pilot would otherwise be repeated on every object. Unattended: build the pilot, record the open questions in `kit.md`, and continue with the style file the pilot's reviews produced.
3. **Conveyor.** Run the remaining `asset` entries through concept-asset-builder in parallel (one builder agent or session per object and engine, each on its own files), each with: its sheet, the scene style file, the pilot's code as the style library, the shared frozen studio. Each object goes through its own review rounds. Show the owner results in batches with a line-up next to the pilot at true relative scale; new general remarks go into the style file for the next objects (re-run earlier objects only if the owner asks).
4. **Composite objects.** Build the parts of a decomposed object through the conveyor, then assemble them from the `assembly` block, and check the whole (contact, gaps, scale between parts, defect pass 5.4) before it enters the scene.
5. Finished assets export as GLB (concept-asset-builder Phase 7: bake per part, join after) into the kit with their kit id; the scene builder places them like any other kit asset.

Before the first iteration of an asset, read its section in `references/field-lessons.md` (rules and recipes from
real runs: grass, roads, water, trees, buildings, light, performance, porting between engines).

Order by screen share and dependency:
ground (tiles or terrain mesh) → surface materials → elevation (height levels, hills, cliffs) → paths (roads, rivers, bridges) → ground scatter (grass, tufts, pebbles) → vegetation → rocks → buildings → ruins and debris → backdrop.

### 5.1 Per-asset loop

For each asset, up to `max_asset_iterations`:
1. Build or regenerate it.
2. Capture `kit_<id>`.
3. `compare.py sheet reference.png render.png` (from `art-direction-pass`), or any side-by-side image, and LOOK at it.
4. Fix the biggest 1–3 differences: silhouette and proportions first, then materials, then detail.
   - When the user says it is far from the concept: first write how the concept looks, how ours looks, and the 5 main differences with a fix each.
   - Add a new feature at low strength and measure its share against the concept (area of dust, cracks per metre, stone count); first passes at full strength overshoot.
   - Matching colour statistics is not matching the look: compare 3x crops and structure metrics too.
5. Run the defect pass (5.4) on the result. Fix what it finds before anything else; never report an iteration that has not passed it.
6. Log in `docs/art/kit.md`: status (draft / matched / accepted with gaps), remaining differences, which defect checks ran.

For assets with high screen share, also run a fresh blind reviewer (a subagent, or a separate session when the tool has none; reference, close crops, the defect checklist and the render only) before marking them matched; guard its verdict with metrics measured on the same crops (luminance quantiles, hue/value of the region, share of each feature such as dust or cracks, element counts). `asset` entries get their review loop from concept-asset-builder (5.0) instead. If the user reviews the renders themselves and asks for no subagents, skip the reviewer, never the defect pass.

### 5.2 Engine-procedural assets

- Tiles (grid concepts): prism with beveled top edge, side band with its own material if the concept shows one, height levels as stacked prisms; cliff sides with displaced rock material.
- Terrain (free-form concepts): heightmap mesh built from `terrain.heights`, surface materials blended by masks from `terrain.regions`, soft transitions; cliffs as separate meshes where slopes are steep.
- Ground surfaces: noise-driven albedo and roughness; break tiling at gameplay distance with world-space macro noise.
- Colours: sample the concept (hue/luminance quantiles of the region), not the user's words. Mind colour spaces (sRGB uniforms vs linear literals). Fade sub-pixel detail (joints, bump) with distance and cap the bump tilt.
- Grass and scatter: instanced cards or small meshes, density and colour range from the concept, slight per-instance hue/value jitter. For full-coverage grass use camera-following GPU blades (recipe in `references/field-lessons.md`).
- Water: match the concept (glossy resin, realistic, stylised flat); visible bed if the concept shows one.
- Roads: mesh or decal along a spline (through cell centres on grids), with edge wear and kerbs if the concept has them.

### 5.3 Blender assets

- One script per asset family: `tools/blender/kit/<family>.py`. Parameters at the top, `--seed` and `--out` from the command line, deterministic.
- Export GLB: metres, Y-up, applied transforms, pivot at base centre, names `<id>_<variant>`. `bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_apply=True, export_yup=True)`.
- Respect `tri_budget`. Bevels and weighted normals on hard surfaces; no subdivision for its own sake.
- Trees: trunk/branch curves + clusters of displaced blobs (broadleaf), stacked noisy cones (conifer); vertex colours or a small gradient material for value variation.
- Rocks: displaced icosphere → decimate → bevel; moss via a top-facing mask.
- Buildings: modular parts (walls, window bands, roller doors, roof units, pipes, ladders, chimneys) assembled by parameters; ruins reuse the same parts with breaks and a debris scatter.
- Keep the scripts: regenerating variants must never require manual Blender work.
- Encode placement rules as build-time checks that fail the script (not warnings): ladders, pipes and signs never cross windows or doors; windows are derived from the same column grid as the pilasters (one opening per bay); doors and their canopies stay below window bands; parts stay inside the footprint or tile; roof equipment fits inside the parapet. Every defect found in 5.4 that a rule could have caught becomes a new check.

### 5.4 Defect pass (before every report)

The wide `concept_view` hides defects: an element of a few pixels there can be absurd up close. For every asset changed in the iteration:
1. **Look up close, from every side.** Crop the `kit_<id>` render at 100 % and render the asset from at least three sides (front-left, both side walls; orbit or extra kit presets), plus one close orbit view of it in the scene. Look at all of them, not only the side-by-side with the concept.
2. **Function and logic.** Doors at ground level and leading somewhere (no gates on upper floors, no door into a wall); ladders and stairs reach a roof or floor and do not cross windows, doors or pipes; pipes connect to something; awnings and canopies sit over openings; windows not blocked by props; openings follow the structural grid (windows and doors between columns/pilasters, never across them; pipe risers on columns, not across windows; columns stop on a lintel above wide gates); every building has a visible entrance on a side the game camera sees; attached parts (awnings, canopies, brackets, signs) touch the wall and their supports, with no gaps.
3. **Counts and scale against the reference.** Count repeated elements (roof units, windows, chimneys, branches, stones) and compare with the concept; extra copies read as clutter. Check sizes against neighbours (door vs storey height, ladder rung spacing, tree vs building).
4. **Contact and fit.** Nothing floating or sunk, no parts hanging over the tile/cell edge, no interpenetration (pipes through walls, trees through roofs), no z-fighting.
5. **Patterns at close range.** Procedural surfaces must not read as tiles, a mosaic or stained glass (voronoi cells with flat colour and dark outlines are the usual culprit), and must show no visible repetition or seams.
6. **Material logic.** Light and dark parts where the real object has them (frames, copings, caps, edges); weathering where water and dirt actually collect.

In the report, say what was checked and what was found; list anything left unfixed instead of calling the asset done.

## 6. Phase 5 — Assemble the golden scene

Assemble only after the pilot is accepted and the conveyor objects have passed their reviews; the final light/shadow/post pass (Phase 6) happens on the assembled scene, never per object.

1. Build the concept layout with the scene builder.
2. Capture `concept_view`; make a side-by-side sheet and a 50% blend with the concept.
3. Fix LAYOUT errors first (wrong cell types or regions, heights, path routes, missing or misplaced objects), then proportions of assets in context, only then style.
4. Check every signature trait; list any that is not yet present.
5. Run the defect pass (5.4) on the assembled scene with close orbit views of each area (assets in context reveal new problems: overlaps, scale, placement on tiles).

## 7. Phase 6 — Look and light

Run `art-direction-pass` with `scope=global,environment`, the scene concept as reference and `concept_view` as the main preset (plus `gameplay_wide` if it exists). If that skill is not available, follow the same loop: one parameter group per iteration, a fresh blind A/B reviewer, keep or revert within the Git rules above, 5–12 iterations. Keep the review blind: shuffle before/after into A and B per preset, copy them with the concept into a temporary folder outside the project, keep the mapping in the project, and give the reviewer only the paths of those files.

Lighting and post tuning happen there, not inside asset building. Do not compensate for a weak asset with lighting.
- Faces turned away from the key go near-black: add a shadowless low fill light from the mirrored side and re-check the median.
- Depth of field is relative to the focus distance, weak, toggleable, and keeps gameplay objects out of the blur.
- Once the user starts asking for "a bit less of X", build a live tweak panel generated from the shader uniforms.

## 8. Phase 7 — Deliver

- `docs/art/kit.md` — every asset: status, how to regenerate it, remaining gaps.
- `docs/art/layout/README.md` — how to author a new map or level in the layout format and build it.
- `docs/art/scene-final.md` — concept vs golden scene sheet and blend, signature-trait checklist, remaining discrepancies and why, performance (draw calls, instance counts, frame time on `concept_view`).
- One commit per finished asset family and per scene iteration (or a `kit.md` record each, per the Git rules above).

## 9. Constraints

- No units, mechs, characters or vehicles.
- Everything reproducible from data and scripts; no manual-only steps.
- Performance: instancing for scatter and repeated tiles, shared materials, LOD or impostors for dense forests if needed. Report frame time. Profile by switching features off one at a time (draw calls are a poor proxy); never time while another render or agent uses the GPU. Never auto-decimate to a triangle cap: use a failing budget check.
- The runtime scene is interactive by default (zoom/orbit work at once); the report gives the run command and controls. Animate at runtime, freeze time in captures.
- Do not distort the camera, the grid or object scales to win a pixel match. Grid layouts must stay on a regular grid.
- Never claim a match without a render you looked at.
- Never report a change as done before the defect pass (5.4) has run on it.

## 10. Engine notes

**Godot 4**: MultiMeshInstance3D for grass/scatter/forests; a heightmap ArrayMesh built from the layout for free-form terrain (or the terrain plugin the project already uses); GLB import with materials replaced by presets; if the concept has a miniature look, tilt-shift via CameraAttributesPractical DOF (near/far blur around the board centre) or a screen-space shader blurring by vertical distance from a focus band; StandardMaterial3D with transparency + refraction or a custom shader for water; `--headless` does not render.

**Three.js**: InstancedMesh for scatter; PlaneGeometry displaced from a heightmap for free-form terrain; GLTFLoader; MeshPhysicalMaterial (transmission, roughness, ior) for water; miniature tilt-shift as a custom ShaderPass (vertical gradient blur) or BokehPass; capture via Playwright headed with `preserveDrawingBuffer: true`.

## 11. Templates

Invoke by path from the project root (requires Pillow and numpy). `compare.py` and the capture harness come from `art-direction-pass` when it is installed.

- `scripts/grid_overlay.py CONCEPT --grid hex|square --orient pointy|flat --cols N --rows M --corners "x,y x,y x,y x,y" [--cell-m METRES] -o overlay.png` — projects a grid through the four corner pixels (TL TR BR BL of the grid's bounding box as it appears). Labels are axial `q,r` (hex) or `col,row` (square); with `--cell-m` a square grid becomes a measurement grid whose labels are the metre coordinates of each cell's centre. Corners that are repeated, collinear or out of order are rejected. The board is a plane: raised tiles look shifted.
- `scripts/crop.py SHEET boxes.json -o docs/art/reference/kit/` — `boxes.json` is `{"tile_grass": [x0, y0, x1, y1], ...}` in sheet pixels; names must be plain file names, and all boxes are checked before anything is written.
- `scripts/blend.py CONCEPT RENDER -o out.png [--alpha 0.5]` — overlays the render (resized to the concept) for camera and layout alignment.

Tests of the tools themselves: `python3 -B -m unittest discover -s .claude/skills/concept-scene-builder/scripts` (skipped without Pillow and numpy).
