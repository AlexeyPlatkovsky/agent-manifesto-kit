# Field lessons (real runs: post box pilot, 6 owner rounds + 2 agent experiments; vending machine via the conveyor)

## Results to calibrate expectations
- Post box, hand-iterated with the owner: silhouette IoU 0.84 → 0.96 after measuring; independent reviewer 4–6.5 → 7.5/10 over 3 rounds; the owner still found 7 issues per round for 3 more rounds, mostly wear.
- Post box, agents + Codex reviewer, no owner: three.js 5 → 7, Blender 6 → 6.5 (reviewer v1, no rubric, no memory).
- Vending machine from scratch through the conveyor (style file + reviewer v2): Blender 6.3 → 6.9 → 7.1 → 7.2, three.js 6.25 → 6.85 → 6.9 → 6.9; none of the pilot's owner complaints repeated. Shape 8–9, paint 8, parts 7–8, chips 6, drips 5–6.
- Two-storey shop (8 × 6 m, rooms inside), one Blender builder, ~2.5 h: 6.99 → 7.44 → 7.87, final 7.92; shape and interior 9, roof/shop front/openings/plaster 8, stains 6. Accepted by the owner without remarks.

## Measuring
- Geometry measured from pixels beat eyeballing immediately (IoU 0.84–0.93 on the first build). The two corrections later were base height (a contact shadow is part of the silhouette) and body radius.
- Count facets from the sheet: the owner had to point out "equal-sided octagon", not a 16-gon.
- Metric masks lie unless resolution-normalised: a 15 px window meant 3.8 cm on the concept and 1.9 cm on 2x renders, the reviewer believed "half the rust" and kept asking for more. Normalise scale, use windows in metres, drop vertical components > 20 cm (edges, grooves), overlay masks and look.
- Silhouette masks must exclude the ground shadow (background scaled by a near-constant factor).
- Colour statistics matching is not the look matching; the reviewer and close-ups decide.

- Wear darker than the surface (peeling plaster over a darker layer) was invisible to a "lighter than the paint" chip mask; with a median reference it caught only patch edges, because a third of the wall was peeled. A high-percentile reference in a ~1 m window fixed it; goods behind shop glazing read as "moss" until the glazing was excluded per view.
- Coverage saturates above ~40% of a local window: the builder could not raise the measured number further even when the eye said enough. Give ranges and trust the overlay.
- Back and side positions written in image coordinates mirrored a whole façade; measure in object coordinates per view.
- Owner constraints (8 × 6 m, 3 m floors) disagreed with the generated sheet (a floor seam at 3.45 m); without a separate constraints block the builder had to decide which to trust.

## Reviewers
- Without a rubric and memory, the reviewer contradicted itself between rounds ("lips overloaded" → "lips too fresh") and gave the same score four times while major issues dropped from 9 to 6. A weighted rubric computed by a script + the previous review + the builder's decisions log fixed it: monotonic scores, no reversals.
- A reviewer of the same model that also built the thing anchors on its intentions; use another model or a fresh context with only the inputs.
- The reviewer trusts numbers it is given; give it only numbers you have validated by overlay.
- The owner's eye still catches things the reviewer does not (mould on a hood, a too-white sign, a door that reads noisy, sharp three.js edges). Keep the owner checkpoint on the pilot and on wear.

- The reviewer can only judge what it sees: an interior got a 9 only because the builder rendered floor-plan cutaways and a section through the stair as extra images.

## Textures from image models
- A generated asset sheet drew peeling plaster as a regular diamond lattice: shape and layout were usable, the wear was a stamp. Name the scene concept as the wear reference.
- Albedo textures from Codex image generation are good paint bases but bake in chips, moss, stains and "panel seams". One cap texture had 23% chips (concept ~8%) and was unusable. Clean with hue/lightness filters; never let the texture carry the wear.
- Box-projected textures sample random parts of a texture: a cap's top faces sampled the mossy bottom band → "mould on the cap". Map each part to a clean band of the texture.

## Light, colour, engines
- Lights must turn with the camera (the concept sheet lights every view the same way); otherwise back views are 30% darker.
- AgX/ACES desaturated or shifted the red; Standard (Blender) / Neutral (three.js) kept the albedo hue. Exposure was the first big fix (renders were pink and clipped).
- Joining parts before baking made the Bevel/AO masks treat joints as edges → light outlines around the hood and the sign ("over-sharpened, noisy edges" in the engine). Bake parts separately into one atlas, join after.
- Baked AO + runtime AO = double darkening. Calibrating the engine with a material colour multiplier tinted chips and the sign blue; calibrate with light/exposure.
- Tone mapping darkened the page background in three.js (and only for one viewer, which made it look "too dark"); compensate the background or composite it.

## Process
- Words before code: when a result is "far from the concept", write how the concept looks, how ours looks, and the top differences with one fix each.
- New effects at low strength first; every full-strength first pass overshot.
- Debug masks by rendering the mask itself (white on black / emission) — two "invisible effect" bugs were a noise Scale left at the default (5× too fine) and a falloff region too small to cross the threshold.
- Builders as fresh agents with a written brief take 40–95 minutes per object and engine; run engines in parallel, give each its own files, and let them log deviations from the spec.
