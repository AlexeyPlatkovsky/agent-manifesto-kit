---
name: blender-mocap-retarget
description: Rig, skin and retarget an existing motion-capture or library clip (for example Mixamo FBX) onto an existing Blender character without changing the character, then verify and export it for a game engine. Use when adding source animation to a finished model; not for modeling, and not for hand-keyed animation from scratch.
---

# Blender Mocap Retarget

## Scope

Rig, skin and retarget source motion onto an existing character while preserving its appearance.
Work to the task's motion, root displacement, loop and delivery criteria. Profile selection,
independent review and bounded repairs are owned by `../blender-asset/workflows/asset.yml`;
adding animation does not require restarting the modeling workflow.

## Prerequisites

- Install the complete `blender-3d` bundle; its sibling skills and workflow are required context.
- Install [Blender](https://www.blender.org/download/); verify `blender --version`.
- Install [Python 3](https://www.python.org/downloads/) and `python3 -m pip install Pillow numpy`
  for sibling [Pillow](https://pillow.readthedocs.io/) / [NumPy](https://numpy.org/) image helpers; verify `python3 -c "import PIL, numpy"`.
- Only for a required Godot check: install [Godot 4](https://godotengine.org/download/) and
  verify `godot --version`; set `GODOT` if the executable is not on `PATH`.
- Resolve script paths from their skill directories; keep executable paths in consumer config.

## Invariants

- Do not remodel. The rest pose must render identically to the unrigged model: render
  baseline views before rigging and diff them against rest-pose renders afterwards. If deformation truly needs geometry (for example extra loops at joints), add it
  without changing the rest-pose renders, and show the diff.
- Build the armature on the character's own joints. Never stretch the character to the source
  skeleton; absorb differences in the retarget.
- Modular objects stay separate. Each deforming part gets its own Armature modifier; rigid
  equipment follows one bone (or a socket bone) with full weight.
- Keep the source clip, and any imported source rig, out of the export: use a separate hidden
  collection or a separate file.
- Use a persisted script for rig, weights and retarget, so the result can be rebuilt.

## Tools

Scripts in this skill's `scripts/` folder (Blender scripts run with `blender -b ... --python`):

| Script | Purpose |
| --- | --- |
| `inspect_motion_source.py` | Skeleton, fps, frame range, rest pose, root motion, foot height offset, loop seam of the source |
| `check_motion.py` | Ground penetration, planted-foot slide, interpenetration beyond the rest baseline, loop seam |
| `render_frames.py` | Frame renders from several angles with following cameras and a checker floor |
| `export_gltf_clip.py` | GLB export with exactly one clip per named action |
| `verify_gltf.py` | Re-import; check requested mesh/skin/rig requirements and clip timing; `--exact-clips` rejects extra or missing original clip names |
| `godot_verify.py` | Optional: headless Godot import of the GLB, checking meshes, bones, clips and key timing |

The sibling skill's scripts are used too, at `../blender-reference-model/scripts/` relative to
this skill's folder (not the working directory): `render_views.py` and `diff_renders.py` for the
rest-pose check, and `contact_sheet.py` to tile frame renders.

## Procedure

Apply Stop Conditions immediately during every step; return the blocked work and evidence gaps.

1. Capture baseline views with the character's spec (or a spec that frames the asset), using
   reproducible render settings. Identify authoritative asset, source clip, output and allowed edits.
2. Inspect source fps, range, rest pose, root motion and loop structure. Select and record root
   motion deliberately: preserve source distance, scale proportionally, or make in-place.
   Do not change the requested displacement merely to hide foot slide.
3. Build the rig on the character's joints and retarget rest-relative rotations. Account for
   source offsets and scale. Use foot constraints/IK only as needed; compare source and target
   at aligned phase/time, including a non-looping end when relevant.
4. Skin deforming regions with appropriate blend zones; bind rigid attachments to their intended
   bones/sockets. Correct observed collisions with the smallest local adjustment. Outward arm
   offsets, clavicle damping and prop swing are optional measured corrections, never defaults;
   preserve source performance and verify each correction against it.
5. Repeat the baseline rest-pose renders with identical settings and run `diff_renders.py`.
   A difference outside the agreed tolerance fails appearance preservation.
6. Run `check_motion.py` on named feet, pairs and frame range. Record coverage and statuses.
   Choose task-specific ground, planted-slide, overlap and loop tolerances; do not apply walking
   or looping criteria to a jump or non-looping clip. Strict mode needs at least one threshold
   and fails unmet thresholds or missing requested coverage. Run with `--python-exit-code 1`.
7. Inspect affected frame contact sheets at the intended size, including representative contacts,
   transitions and extremes. Missing views cannot prove motion continuity; report sampling limits.
8. For requested exports, isolate intended actions and export. Use `verify_gltf.py` with
   `--expect-clips Walk,Run --exact-clips` (substitute the contract's exact names) and the required
   `--require-mesh`, `--require-skin`, `--require-rig` flags. For a static export the expected clip
   set is empty. Run target-engine checks when required by the contract.
9. Return motion evidence and unresolved defects after this stage. The companion workflow
   decides review and any further reserved repair; it does not require fresh modeling.

## Stop Conditions

Missing authoritative assets/source, conflicting displacement requirements, or a required
appearance-changing edit outside scope blocks the affected work. Mark missing tool/check
coverage `not_tested`; never claim delivery acceptance with a missing required check or review.

## Known Pitfalls

- Blender 5.x stores animation in layered actions. F-curves live under
  `action.layers[].strips[].channelbags[].fcurves`; `action.fcurves` no longer lists them.
- Mixamo FBX armatures import with object scale 0.01, and a walk's feet can sit above the rest
  pose (about 1.4 cm in Mixamo's Walking). Subtract that offset before scaling, or feet float.
- Exported clip time counts from scene frame 0, so an action that starts at frame 1 arrives
  offset by one frame. Put each action on its own NLA track, named after the clip, with the
  strip at frame 0, and export in `NLA_TRACKS` mode. Confirm the first key is at time 0 with
  `verify_gltf.py` or `godot_verify.py`. In the sessions this came from, `ACTIVE_ACTIONS` named
  the clip "Animation" and `ACTIONS` also exported stray source actions.
- For a loop whose last frame repeats the first plus one stride, set the scene range to exclude
  the repeated frame, so playback does not stutter.
- Overlap tests between adjacent regions of one mesh report shared edges. Pair regions that
  should never touch.

## Output Contract

`Skill: blender-mocap-retarget - output below`

Report source facts and root-motion mode; editable asset and persisted script; rest-pose diff;
motion-check statuses, thresholds and sampled frames/objects; source/target contact sheets;
requested export/engine verification; unresolved defects and missing evidence. Distinguish
technical pass from visual judgment and engine checks that have not run.
