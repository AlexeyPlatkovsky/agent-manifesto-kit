# Builder brief — <OBJECT> (<PIPELINE>)

Fill the <...> fields, save as brief/agent_brief.md in the object workspace and pass it to a fresh builder agent
(one per engine). Write the brief in the owner's language; the builder writes its report in it too.

You build **from scratch** (or improve, if `out/baseline/<PIPELINE>` exists) a 3D model of <OBJECT> so that it matches
its concept sheet as closely as possible and keeps the shared style of the scene <SCENE>. The scene style rules were
agreed with the owner on earlier objects: they are mandatory.

## Workspace
`<ABSOLUTE WORKSPACE PATH>` — work ONLY inside it and only in your pipeline's files:
<PIPELINE FILES, e.g. blender/build_object.py + new helper modules in blender/, out/blender/*, reports/blender.md,
reviews/blender_decisions.md, textures/blender_*>. Do not edit the frozen studio (<blender/studio.py,
blender/render_views.py | threejs/studio.js, threejs/index.html>). Another builder may work in parallel on another
pipeline; never touch its files or anything outside the workspace.

## Inputs (read only)
- `reference/concept.png`, `reference/crops/{3q,front,back,left,right,detail}.png` — look at them at 2x.
- `spec/object.json` — measured geometry, palette, cameras. It is a draft: if you find a clear error, do not edit it;
  log the deviation in `reviews/<PIPELINE>_decisions.md` and apply it in your code.
- `brief/wear_description.md` — numeric target per zone, part and side (source of truth for the surface).
- `brief/scene_style.md` — scene style rules (mandatory). `brief/rubric.json` — how the reviewer scores you.
- Style library (read only, copy functions): <paths to approved objects of this scene, or the skill's
  references/examples/>. Keep the scene's wear language; adapt colours.

## Pipeline mechanics
<Blender: binary path; build `Blender -b --factory-startup --python blender/build_object.py` (spec Y-up/front +Z ->
Blender (x, -z, y)); finish with `studio.setup(SPEC); studio.save(ROOT, "object")`; render
`Blender -b --factory-startup blender/object.blend --python blender/render_views.py -- --samples 32` (96 for finals)>
<Three.js: vite server rooted at the workspace on http://localhost:<PORT>; implement threejs/model.js
`export async function buildModel(spec)` (Y up, front +Z); capture `node tools/capture.mjs threejs --base http://localhost:<PORT>`>

## Tools
- `tools/gen_texture.sh <out> <WxH> <x|xy|none> "<description>"` — optional paint/concrete/metal base textures via
  Codex image generation; clean baked-in chips/moss/stains, wear must come from the procedural layer.
- `python3 tools/wear_stats.py out/<PIPELINE>` vs `out/wear_stats_concept.json` (read the caveats in the description).
- `python3 tools/metrics.py <PIPELINE>` — silhouette IoU and zone ΔE vs the concept.
- `python3 tools/sheet.py <out.png> <views> <PIPELINE> <scale>` — concept | render sheets.
- `tools/codex_review.sh <PIPELINE> <round>` — independent reviewer (another model, read only): sees the concept, your
  renders, the description, the style, the rubric, the measurements, its previous review and your decisions log.
  Writes reviews/<PIPELINE>_r<round>.md and .json (weighted score). 3–10 min: run in the background and wait.

## Process
1. Study the concept, spec, description, style. Write your plan into the report: parts, materials, how you do wear.
2. Geometry (all edges rounded, nothing intersects or floats) → materials → wear → render 5 views → self-check
   (sheets, 2x close-ups of every part, measurements, IoU/ΔE).
3. Keep `reviews/<PIPELINE>_decisions.md` up to date (the reviewer reads it).
4. Review rounds 1..<N> with fixes after each; stop early at a weighted score ≥ <TARGET>. After the last round only
   obvious small fixes.
5. The goal is visual match with the concept and the scene style, not tuning numbers.

## Deliverables
- `out/<PIPELINE>/{3q,front,back,left,right}.png`.
- `reports/<PIPELINE>.md`: plan; per round — changes, weighted score and per-criterion scores; final per-criterion
  table; deviations; time spent; what got in the way (tools, review, spec).
- Final message: short summary — scores per round, what works, what does not.
