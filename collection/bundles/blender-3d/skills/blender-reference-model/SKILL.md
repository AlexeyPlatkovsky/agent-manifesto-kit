---
name: blender-reference-model
description: Build or revise a game-ready low-poly Blender model that must match a supplied reference image (turnaround or orthographic views) as closely as possible. Use for scripted Blender modeling from a reference sheet; not for rigging or animation, and not for free concept design.
---

# Blender Reference Model

## Scope

Build or revise a model against supplied reference views. The reference is authoritative except
for explicit requested deviations. Return editable source and evidence for the task contract;
profile selection, review and bounded repair are owned by the companion
`../blender-asset/workflows/asset.yml`. A direct invocation needs the same explicit acceptance
criteria and required evidence; do not invent a universal quality target.

## Prerequisites

- Install the complete `blender-3d` bundle; its sibling skills and workflow are required context.
- Install [Blender](https://www.blender.org/download/); verify `blender --version`.
- Install [Python 3](https://www.python.org/downloads/), then `python3 -m pip install Pillow numpy`;
  verify `python3 -c "import PIL, numpy"`. [Pillow](https://pillow.readthedocs.io/) and
  [NumPy](https://numpy.org/) run with system Python, outside Blender.
- Store executable paths and project conventions in the consumer project.

## Invariants

- Build through a persisted Python builder run with `blender -b`; no unrecorded manual edits.
  Rebuilding must reproduce the model. If the user edits the `.blend` by hand, that file becomes
  authoritative: never rebuild over it; build into a new file and reconcile.
- Preserve project units, axes and origins. For a new character with no conventions, record
  metres, Z up, facing -Y and ground origin as defaults before building.
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

## Procedure

Apply Stop Conditions immediately during every step; return the blocked work and evidence gaps.

1. Confirm task criteria, reference priorities and requested deviations. Draft and confirm the
   spec; set `meters_per_px` from the intended dimensions. View names/cameras are guesses until
   checked against the sheet labels. Record conflicting views instead of averaging silently.
2. Measure silhouettes and primary forms before adding detail. For a revision, preserve accepted
   geometry and start from the authoritative asset; edit only the scoped region.
3. Render selected views at the reference scale. Use `compare.py` and `edges.py` to identify
   differences, and report per-view IoU as a diagnostic. Acceptance uses the task's tolerances,
   identity features and intended display size; no fixed IoU score guarantees completion.
4. Inspect relevant interior details with `zoom.py` (for example a prop latch, face or equipment
   attachment). Inspect colours when colour fidelity is required, respecting requested changes.
5. Render additional angles only where needed to test required visibility, construction or
   changed dependencies. Check for floating parts, poke-through and unfinished surfaces.
6. Run `mesh_report.py` for the agreed object scope and assess the task's topology/material/size
   constraints. Explain intentional open edges. Export and re-import only when export is a
   deliverable; record unrun required checks as `not_tested`.
7. Return current evidence and concrete remaining differences after this build or repair stage.
   The companion workflow owns further repairs and independent-review gates.

## Stop Conditions

Missing essential references, unresolved priority conflicts or an overwrite of authoritative
hand edits block the affected work. Missing required evidence blocks acceptance. Return the
specific gap; do not quietly weaken criteria or keep iterating past the reserved repair stage.

## Known Pitfalls

- A flat plate placed on a lofted, curved surface gets swallowed by the bulge. Make pockets,
  flaps and patches follow the surface.
- Colours sampled from the reference are display (sRGB) values, and Blender's Base Color is
  linear: convert before use. Lighting then shifts the rendered value either way, so treat the
  first material colours as a starting point. Judge `colors.py` ratios against the task's
  colour tolerances within the reserved stage. Preserve agreed colour management; Standard
  can help untonemapped comparisons, while Filmic/AgX changes the displayed colour response.
- AI-generated turnaround sheets often disagree slightly between views (head height, prop side).
  Match the priority the user set, and report the conflict instead of averaging silently.
- A rigged model renders in its animated pose unless the armature is set to rest.
  `render_views.py` does this by default.

## Output Contract

`Skill: blender-reference-model - output below`

Report the editable `.blend` and persisted builder/edit script; selected comparison views with
per-view IoU; relevant detail/extra-angle evidence; scoped mesh/check statuses (`pass`, `fail`,
`not_tested`); requested export evidence; intentional deviations and unresolved differences.
List required evidence that is missing. Do not imply unrendered views or untested engine imports
passed. Evidence paths feed the companion workflow's review and completion gates.
