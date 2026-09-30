---
name: blender-mocap-retarget
description: Rig, skin and retarget an existing motion-capture or library clip (for example Mixamo FBX) onto an existing Blender character without changing the character, then verify and export it for a game engine. Use when adding source animation to a finished model; not for modeling, and not for hand-keyed animation from scratch.
---

# Blender Mocap Retarget

## Outcome

The existing character performs the source motion on its own skeleton, with its proportions,
materials and modular parts unchanged. Feet plant without sliding or sinking, limbs clear the
body and equipment, the loop is seamless, and the export plays exactly the intended clips in the
target engine.

## Invariants

- Do not remodel. The rest pose must render identically to the unrigged model: render
  baseline views before rigging and diff them against rest-pose renders afterwards (Method
  steps 1 and 7). If deformation truly needs geometry (for example extra loops at joints), add it
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
| `verify_gltf.py` | Re-import the export; report meshes, skinned meshes and bones; fail on missing clips or clips not starting at frame 0 |
| `godot_verify.py` | Optional: headless Godot import of the GLB, checking meshes, bones, clips and key timing |

The sibling skill's scripts are used too, at `../blender-reference-model/scripts/` relative to
this skill's folder (not the working directory): `render_views.py` and `diff_renders.py` for the
rest-pose check, and `contact_sheet.py` to tile frame renders.

## Method That Works

1. Before touching the model, render baseline views with `render_views.py` (the model's
   `ref_spec.json`, or any spec whose views frame the character) into a `before/` folder.
2. Inspect the source. Plan from its fps, range, rest pose (T or A), root motion and loop
   structure (library walks often end on the first pose plus one stride).
3. Build the rig with source-compatible bone names (for example Mixamo names without the
   `mixamorig:` prefix) at the character's joints.
4. Retarget each bone's world-space rotation relative to its rest pose, so differing rest poses
   cancel out. Scale root motion by the leg-length or hip-height ratio: that scale is what stops
   planted feet from sliding. Solve feet with two-bone IK (soft limit, no knee pop) toward the
   scaled source ankle, and add a ground pass that keeps soles on the floor while planted.
5. For bulky or equipped characters, add an outward arm offset (larger on the back-swing) and
   damp long clavicles, so arms clear the torso and belt kit. Let hip-mounted props swing with the
   thigh through socket bones.
6. Skin with blend zones at shoulders, elbows, wrists, fingers, hips, knees, ankles and neck.
   Keep hair and beards rigid to the head.
7. Render the rigged model with the same spec (armatures render in rest pose by default) and run
   `diff_renders.py before/ after/`. It must report the views identical within tolerance.
8. Iterate with `check_motion.py` and frame renders from front, side, 3/4, back and close-ups at
   the hips, shoulders and feet. Targets that worked: ground within about 3 mm, planted-foot slide
   of a few mm per frame, no interpenetration beyond the rest baseline, zero rotation difference
   at the loop seam.
9. Export with `export_gltf_clip.py`, then run `verify_gltf.py`, and `godot_verify.py` when the
   target is Godot.
10. Have the `visual-reviewer` agent review contact sheets of the motion before handing over.
    Include a contact sheet of the source clip at the same frames when you can render it, plus
    the user's requirements. If the reviewer cannot run or cannot view images, say so in the
    evidence.

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

## Evidence To Report

Source facts, the rest-pose identity check, `check_motion.py` results, contact sheets from
several angles, the export verification output, the review findings with their resolution, and
any motion that could only be judged in the engine.
