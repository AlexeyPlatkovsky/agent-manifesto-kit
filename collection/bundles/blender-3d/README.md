# Blender 3D

Build low-poly game models in Blender that match a reference sheet, then retarget library motion
onto them and export clips a game engine plays correctly, using measured comparisons and an
independent visual review instead of guesswork.

## Contents

| Item | Type | Purpose | Depends on |
| --- | --- | --- | --- |
| `blender-reference-model` | skill | Scripted modeling against a reference: measure, render at the reference scale, compare, zoom, calibrate colours, check meshes | `visual-reviewer` |
| `blender-mocap-retarget` | skill | Rig, skin and retarget a source clip onto an existing character; motion QA; single-clip glTF export; re-import and Godot checks | `blender-reference-model` scripts, `visual-reviewer` |
| `visual-reviewer` | agent | Fresh-context review of comparison sheets and motion contact sheets; at most five ranked findings | — |

## Requirements

- Blender run headless: `blender -b model.blend --python script.py -- args` (tested on 5.2; 4.2+ expected)
- System Python 3 with Pillow and numpy for the image scripts
- Optional: Godot 4 on `PATH` (or `GODOT=/path/to/godot`) for `godot_verify.py`
- For Codex, the reviewer agent needs image viewing available in its session; if it is not,
  the skills report that the independent review could not run

Record your Blender and engine executable paths in your project's instruction file, so agents
don't have to search for them.

## Install

The bundle has only skills and an agent, so sync is enough and keeps both tools up to date:

```bash
agentkit sync blender-3d --provider claude,codex
```

Use `agentkit adopt blender-3d --provider <provider>` instead for a one-off copy you intend to
edit locally.

## Provenance

Distilled from two independent end-to-end sessions that built the same reference-matched
character (0.94-0.96 silhouette IoU per view) and retargeted a Mixamo walk onto it. The scripts
reproduce those sessions' measurements on the original assets.
