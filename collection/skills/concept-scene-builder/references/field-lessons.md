# Field lessons (from real runs)

Each rule comes from a correction the user had to make or a fix that worked. Read the section for the asset you are
building before its first iteration. Short rules are repeated in SKILL.md; the recipes live only here.

## Process

- **Words before code.** When the user says an asset is "far from the concept", write how the concept looks, how ours
  looks, and a table of the 5 main differences with one fix each; apply after approval (or, unattended, apply the
  table and keep it in the report). Blind parameter tweaking took several rounds; the table landed in one.
- **"Too X" means measure first.** "Too yellow" was not too much yellow (the concept measured more yellow than ours);
  it was hard transitions: two steep curves, two palettes, ground switching colour under patches. Check transitions
  and contrast before changing amounts.
- **New feature at low strength, then measure its share** against the concept (share of ochre dust, cracks per metre,
  foam area). Every first pass at full strength overshot: dust covered half the road, plates read as cobbles,
  water went opaque, a ford of 52 stones read as a blockage (15 was right).
- **Colour numbers are not the look.** The asphalt median matched the concept to 2 RGB units and the user still said
  "far". Add structure metrics (contrast inside the region, share of each feature) and compare 3x crops.
- **Colours come from the concept, not from the prompt.** The user's words ("mostly green") describe the impression;
  sample the concept (5 hue/luminance quantiles of the region) and set the ramp from them. Fully automatic palette
  fitting diverged; quantiles + gentle correction (strength ~0.6) worked.
- **User overrides beat the concept.** "Asphalt should cover the whole bridge (the concept is wrong here)": record it as
  a contradiction rule in kit.md so no later pass reverts it.
- **Tweak panel early.** When the user starts asking for "3-4x fewer cracks", give every look parameter a name and a
  live panel generated from shader uniforms and profiles (save/reset; strip runtime-only uniforms on save;
  a self-test that a value round-trips).
- **Reviewers.** A blind A/B reviewer sees only the wide view and drifts from measurements (it darkened the grass
  median from 0.45 to 0.37 because "darker looked richer"). Give reviewers close crops plus the defect checklist and
  guard every verdict with metrics. If the user prefers to review renders personally, skip reviewers, never the defect pass.

## Iteration speed and performance

- Iterate on the single-asset preview (seconds); render the full scene last (minutes).
- Never time performance while another render, test or agent uses the GPU.
- Profile by switching features off one at a time. Draw calls fell 882 -> 198 and frame time only 19.4 -> 18.0 ms;
  the real costs were shadows (~7 ms: atlas 8192 -> 4096, cascades 4 -> 2), grass (~6 ms: fewer, wider blades,
  colour conversion moved to the CPU) and SSAO (1.6 ms).
- Never auto-decimate assets to a triangle cap: a cap removed whole walls of ruins. Use a budget check that fails.

## Runtime deliverable

- The scene is interactive by default: zoom/orbit work right away, the report gives the run command and controls.
- Animated effects (water flow, foam) run at runtime; captures freeze time so comparisons stay deterministic.
- Depth of field (tilt-shift) is relative to the focus distance (near ~0.8 d, far ~1.12 d), weak (amount ~0.03),
  with a toggle key, and keeps gameplay objects out of the blur. A fixed band blurred the whole board on zoom.

## Light and shading

- Faces turned away from the key light render near-black (bridge walls at value 0.18). Add a shadowless fill from the
  camera side, mirrored azimuth, low elevation (~10 deg), and re-check the global median afterwards.
- Fade sub-pixel detail (joints, bump) with distance and cap the bump tilt: 5 cm joints made masonry black from afar.
- Colour constants must be in the right colour space: in Godot `source_color` uniforms are sRGB, literals in code are
  linear. A grey entered as a bare 0.5 rendered almost white ("white dots"). A shared effect (chips, grime) changes
  every asset that uses it: re-check all of them after a change.
- Give each material role its own material (window frames shared the coping material and went dark with it).
- Voronoi cells with flat colour and dark outlines read as stained glass. River bed: separate dome-shaded pebbles on
  sand (distance to the feature point), not cells.

## Recipes

### Camera-following GPU grass (Godot or three.js)

- Every blade is built in the vertex shader from a hash of its world-grid cell: stable under camera motion and LOD.
- Two LOD rings of fixed patches around the focus; cull patches on the CPU against the board and the view frustum.
- Grid sized to the normal density; rejected blades collapse to a degenerate point. ~8 vertices per blade.
- Back faces: reset the normal (double-sided blades flip it).
- One include shared by the ground shader and the blade shader, so the ground under blades has the same colour field.
- Keep-out (roads, rivers, structures) as a baked distance field: interpolates cleanly, edges stay sharp.
- Result: build 1.5 s -> 0.02 s, 27 MB of per-blade data -> 0.2 MB of tables, cost follows screen coverage, not map
  size (100x100 board: 2.4-6.6 ms).

### Broadleaf tree

- Recursive branch skeleton (trunk -> 7-9 limbs -> 3-5 branches -> 2-3 twigs), golden-angle phyllotaxis (137.5 deg),
  gnarl and an up force; low limbs spread 60-70 deg so the crown starts at ~30 % of the height.
- Foliage clusters on twig tips AND along the outer half of limbs and branches; tips only gave a flat high umbrella.
- Crown-centre normals and interior darkening for the foam-clump look.
- Bark without textures: per-vertex (around, along, circumference) coordinates on the tubes + a procedural shader
  (furrows, plates, knots, moss low and on up-facing sides).

### Generators

- Check openings in the mesh, not only placements: an arch notch in one n-gon was triangulated across the opening.
  Build walls with openings from strips.
- Every defect the user finds that a rule could catch becomes a failing build check.

### Camera match

- Do not trust a closed-form homography decomposition for the camera; fit pose and FOV by reprojection error with
  free yaw and roll (AI concepts have inconsistent perspective; ~12 px RMS is normal).

## Porting a kit to another engine (Godot -> three.js)

- Keep one scale constant (kit unit -> game metres) and compute every pattern in kit units (`p_kit = p_world / S`);
  never rescale shader constants by hand. Scale models at load.
- Uniform values live in the material files (.tres), not in the shader defaults: read both.
- Godot light energy E ~ three.js intensity E * pi (physically based lights); ambient colour * energy the same.
- Port surface shaders into the engine's standard material (three.js: onBeforeCompile) so shadows, fog and AO keep
  working; a custom ShaderMaterial only where the vertex stage is fully custom (GPU grass), and then wire shadows yourself.
- Assets made for one board layout need adapting to the game's own map: multi-cell footprints, a bridge length that
  matches the crossing, clear cell centres where units stand, heights from the game's grid. Example: the kit bridge
  crossed a shallow stream at grade; the game's river ran 5 m below the meadow, so the bridge needed abutments and an
  arch down to the water, an oblique plan (bank edges at 30 deg to the road) and a wider deck (units stand on it).
- Vertex colours: check how the source engine reads COLOR_0 before porting. Godot passes the glb values raw and the kit
  shaders converted them from sRGB (`color_srgb`); reading them as linear made walls 2.7x too light.
- Light: compare against the source engine's render of the SAME surfaces in-scene (grass, forest, walls, cliffs),
  not against isolated kit renders on a different background. Tonemapper and screen-space AO differ between engines
  (three.js AO darkens direct light too; Godot SSAO only ambient): calibrate exposure, shadow lift and AO by
  measurement, one preset, then fix remaining per-material gaps in the materials.
- Port per zone with parallel executors only after a written contract (scale, mask functions, material names,
  ownership) and a scaffold where every zone starts as a stub on the old code, so each executor sees a complete scene.
  With several executors on one dev server, hot reload restarts their captures: give each its own server without HMR,
  and treat frame times as noisy (measure with/without the feature, not absolute).
