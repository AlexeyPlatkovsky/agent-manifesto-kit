---
name: blender-reference-model
description: Build or revise a game-ready low-poly Blender model that must match a supplied reference image (turnaround or orthographic views) as closely as possible. Use for scripted Blender modeling from a reference sheet; not for rigging or animation, and not for free concept design.
---

# Blender Reference Model

## Outcome

An editable `.blend` produced entirely by a saved Blender Python builder, whose renders match the
reference in every supplied view, with modular parts as separate objects, clean meshes and a
validated export. The reference is authoritative, except where the user explicitly asks for a
deviation (for example a different colour or hand pose); a requested deviation is not a defect.

## Invariants

- Build through a persisted Python builder run with `blender -b`; no unrecorded manual edits.
  Rebuilding must reproduce the model. If the user edits the `.blend` by hand, that file becomes
  authoritative: never rebuild over it; build into a new file and reconcile.
- Units are metres, Z up, character facing -Y, character's left on +X, origin on the ground.
- Each removable or separately animated part (clothing, boots, belt, pouches, props, hair) is its
  own object, named for its role, with a deliberate origin (attachment point or joint).
- Measure before modeling. Take proportions from the reference in pixels, not from generic anatomy.
- Silhouette overlap is a floor, not the target. It cannot see faces, hands, colours or details
  inside the outline. Those need magnified side-by-side inspection.
- Keep machine paths (Blender and engine executables) in the project's own instructions, not in
  builders.

## Tools

Scripts in this skill's `scripts/` folder. Image scripts run with system Python 3 plus Pillow and
numpy. Blender's bundled Python has neither, so run them outside Blender.

| Script | Purpose |
| --- | --- |
| `measure_ref.py` | Draft `ref_spec.json` (view crops, cameras, ground row, metres per pixel) and print a view's silhouette profile in metres |
| `render_views.py` | Blender: orthographic renders at the reference's pixel scale, transparent background, armatures in rest pose |
| `compare.py` | IoU per view, red/blue overlay sheet, height difference; writes `compare.png` and `compare.json` |
| `edges.py` | Row-by-row edge differences in mm for one view: turns the overlay into concrete corrections |
| `zoom.py` | Magnified reference and render side by side for one region (face, hands, belt, boots) |
| `colors.py` | Sampled colour ratios between the reference and the render |
| `diff_renders.py` | Pixel diff of two render folders, e.g. before and after rigging; exits non-zero on change |
| `contact_sheet.py` | Tile renders into one image for review |
| `mesh_report.py` | Blender: per-object triangles, non-manifold edges, degenerate faces, loose vertices, empty slots |

`refspec.py` documents the spec format. Drafted view names and cameras are guesses: confirm them
against the sheet's labels before building.

## Method That Works

1. Draft and confirm the spec. Set `meters_per_px` from the intended height.
2. Print silhouette profiles for each view and build primary forms from those numbers.
3. Render, compare, and correct from `edges.py` output. Repeat until each view reaches roughly
   0.94 IoU or better, and the remaining red/blue areas are explained (reference perspective,
   stylization, requested deviations) rather than ignored.
4. Inspect zoom crops of the head, hands, torso, belt and boots in every view. Fix identity
   features (hairline, beard boundary, facial planes) even when the IoU is already high.
5. Calibrate colours with `colors.py`, except colours the user asked to change.
6. Render angles the reference does not show (3/4 front and back, low, close-ups) and fix
   poke-through, floating parts and hollow backs.
7. Run `mesh_report.py`, export, and re-import or engine-import the export to confirm it arrives.
8. Before handing over, have the `visual-reviewer` agent review the comparison sheet, the zoom
   crops and the extra-angle renders, then fix major findings. If the reviewer cannot run or
   cannot view images in the current tool, say so in the evidence instead of skipping silently.

## Known Pitfalls

- A flat plate placed on a lofted, curved surface gets swallowed by the bulge. Make pockets,
  flaps and patches follow the surface.
- Colours sampled from the reference are display (sRGB) values, and Blender's Base Color is
  linear: convert before use. Lighting then shifts the rendered value either way, so treat the
  first material colours as a starting point and iterate until `colors.py` ratios are close
  to 1. Render with the Standard view transform; Filmic/AgX shifts colours.
- AI-generated turnaround sheets often disagree slightly between views (head height, prop side).
  Match the priority the user set, and report the conflict instead of averaging silently.
- A rigged model renders in its animated pose unless the armature is set to rest.
  `render_views.py` does this by default.

## Evidence To Report

The final `compare.png` with per-view IoU, the zoom crops, the extra-angle renders, the mesh
report totals, the export check, the review findings with their resolution, and any remaining
known differences from the reference.
