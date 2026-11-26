# Wear language (shared by every object of a scene)

The owner judged this language "like in real life" on the pilot object; the reviewer and the measurements are built around it. Adapt colours to the object (primer, rust, grime from the concept), keep the behaviour.

## 1. Chips — flakes, not paint spots
- Paint flaked off down to primer/metal: ragged edge, small satellite flecks next to it, a thin (1–2 mm) darker rusty rim, often vertically elongated (h/w 1.3–2). Inside a large chip the primer may be slightly mottled.
- Distribution per side: many small (< 2 cm, ~65%), some medium (2–5 cm, ~25–30%), 1–3 large (5–10 cm) — every side, including the back and the sides (an empty back reads as unfinished).
- About half sit on/near edges (facet edges, rims, frames, corners), half on faces. Protruding parts (rings, lids, frames, handles) chip more.
- Never: round or even blobs, "peas" of one size, stamped repeats, chips concentrated as big bright patches (they read as paint spots).

**Blender** (`references/examples/postbox_blender.py`, `weathered_paint`): threshold an anisotropic fractal noise (Object coords, scale ~9/9/4.5 per metre, detail 12, roughness 0.72) at a high value (~0.615); lower the threshold near edges (edge mask, below) for edge chips; a second band slightly below the threshold gives the rim; hand-place 2–4 medium/large chips on bare sides with a spherical falloff that lowers the threshold (`spots`). The vending example (`vending_materials_blender.py`, `paint`) uses size classes from cells; either works if the size histogram matches the description.
**Three.js** (`references/examples/postbox_wear_three.js`, `vending_wear_three.js`): explicit chip placement in a canvas in object/UV space with a seeded RNG (count and size classes from the description, half snapped to edges), each chip shaped by thresholded domain-warped fbm plus a second octave at ~3.5× frequency for a ragged edge, satellite flecks, rim band. Pure per-pixel noise thresholds tend to give either confetti or blobs.

## 2. Edge wear — edges and protruding parts first
- A broken strip of primer 2–8 mm wide along edges, with gaps (on 30–60% of an edge's length), bare grey-brown metal in the very core of the strongest spots. Strength: lids/caps/ridges > rims and frames > handles > body vertical edges > flat faces.
- Real rounded geometry is a precondition: a sharp edge has nothing to wear and looks like cardboard.

**Blender**: edge mask = 1 − dot(Bevel node normal (radius ~1–1.5 cm), geometry normal), broken by a mid-frequency noise; for large radii the Bevel node sees nothing — use a mask from the normal (e.g. the band where the normal turns on a rounded roof). Mix primer, then metal on the strongest band; metal gets lower roughness/higher metallic.
**Three.js**: compute distance-to-edge per vertex or in the wear canvas from the known geometry (facet edges, rims, frame outlines), break it into runs with a 1D noise along the edge.

## 3. Rust drips — clusters from real sources
- Sources only: seams, the bottom of protruding parts (rings, boxes, panels, frames, buttons, handles, vents), hinges, screws. Never a uniform row around the whole object at one height with equal spacing ("comb"), never long streaks (> 15 cm), never thin hairlines everywhere ("wood grain").
- A cluster: a stain at the source 2–2.5× wider than the drip below it (12–25 mm tall, rounded bottom), then 1–5 thin strands; strand lengths follow a bell curve across the cluster (centre longest, may be skewed), typical 3–8 cm, a few up to 12–15 cm; clusters vary in size (0.4–1×) and spacing (roughly half of the possible slots are used).
- Colour: orange-brown in the strand, darker brown at the source; on light paint they read by hue, on red paint by darkness.
- Small parts people look at closely (doors, hatches, slots): drips matter more than abrasion there — heavy wear on them reads as noise.

**Blender** (`drips()` in the post box example): per source (height, max length, optional front half-width, seed): arc/x coordinate cut into ~7.5 cm cells; per-cell white noise picks active/centre/width/size; strands from 1D noise along the arc at ~150 cycles/m; length = maxlen · exp(−2.6 t²) · jitter(0.55–1) · size.
**Three.js**: the same model per pixel in a canvas (the post box example), strands 2–3.5 mm wide so they survive the capture resolution.

## 4. Grime and mould
- Olive grime/mould only where water and dirt collect: the bottom 5–10 cm of the body, feet, plinths, ledges of the base. Never on lids, hoods, panels, doors or rings.
- Generated textures often carry green/brown patches: remove them with a hue filter on the parts that must stay clean.

## 5. Signs, marks, small details
- Dull, not fresh: off-white/cream instead of white, slightly soft edges, a few small chips through to the paint, light grime.
- Openings (slots, windows, pickup flaps) stay crisp: little wear right at the opening edge, a visible inner floor/lip, dark brown rather than pure black inside.
