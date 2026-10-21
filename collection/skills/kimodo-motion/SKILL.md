---
name: kimodo-motion
description: Generate humanoid animation clips locally with NVIDIA Kimodo (native kimodo.cpp build) from a text prompt, optionally starting and ending in given poses (key-pose constraints taken from a rig's existing clips), check them numerically and visually on Kimodo's own skeleton, and retarget them onto a Mixamo-named Blender rig. Use when a clip nobody provides is needed (a draw, a gesture, a transition between two existing poses); not for editing captured clips or for finger animation.
---

# Kimodo Motion

## Scope

- Text-to-motion takes on Kimodo's SOMA30 skeleton, several seeds per prompt, with optional start/end key poses
  taken from a rig's own clips, so a take starts and ends where the neighbouring clips do (no cut/settle/blend).
- Numeric gates (key-pose error), frame sheets for a reviewer, a bake onto a Mixamo-named rig with a direction check.
- Out of scope: fingers and props (Kimodo has neither), mid-clip keys (the patch reads `end-effector` keys on any
  frame; `generate` keys only the ends), root2d paths (not supported), engine integration, loop clips.

## Prerequisites

- [kimodo.cpp](https://github.com/localai-org/kimodo.cpp) at `ed8a931` (Apache-2.0) with
  `<skill>/patches/kimodo-cpp-keyposes.patch` (`git apply`). It adds `kmd-generate ... --constraints FILE`, which reads
  upstream Kimodo's constraints JSON (`fullbody`, `end-effector`, `left/right-hand/foot`). Build (C++23, CMake 3.25+;
  verified CPU-only on macOS, Vulkan per its README on Linux):
  `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DKIMODO_ENABLE_VULKAN=OFF -DKIMODO_BUILD_TESTS=OFF && cmake --build
  build --target kmd-generate`. Verify: `build/kmd-generate` prints a usage line with `--constraints`.
- Models: `scripts/download_gguf_weights.sh --output "$PWD" --model soma-rp-v1.1` (needs the `hf` CLI). Keep the
  NVIDIA Open Model License and Meta Llama 3 notices. Verify: `ls "$KIMODO_ROOT"/models/*.gguf` shows the
  motion and text files the defaults (or `KIMODO_MOTION_GGUF` / `KIMODO_TEXT_GGUF`) name.
- Environment: `KIMODO_ROOT` (that checkout); `KIMODO_GENERATE`, `KIMODO_MOTION_GGUF`, `KIMODO_TEXT_GGUF` when they
  differ from the defaults in `<skill>/scripts/kimodo_motion.py` (relative to `KIMODO_ROOT` or absolute);
  optional `KIMODO_EXPORT_GLB` (its `scripts/export_glb.py`: a skeleton GLB per take).
- [Python 3.10+](https://www.python.org/downloads/), standard library; sheets need Pillow
  (`python3 -m pip install Pillow`, verify `python3 -c "import PIL"`).
- Key poses and retargeting: [Blender](https://www.blender.org/download/) 4.x/5.x, `BLENDER` = its executable.
  Verify: `"$BLENDER" -b --factory-startup --version`, then `BLENDER=... python3 -m unittest discover -s
  <skill>/tests -v` (the round trip skips without `BLENDER`).

## Inputs

- Prompt, length `F` in frames (30 fps), seeds (3-4), output dir; for key poses: the rig `.blend` (one armature,
  Mixamo names with prefix `mixamorig:` unless `--prefix` says otherwise, facing -Y) and the clips whose poses start
  and end the take (action-only `.blend` files, with a frame).

## Procedure

`<skill>` is this skill's installed folder; commands run from the consumer project.

1. Spec before generating: the prompt (one short sentence of what the body does; wording about the end state made
   takes start in it), `F`, seeds, start/end poses, acceptance (the gates below, the content a reviewer must see).
2. Key poses: `python3 <skill>/scripts/kimodo_motion.py keypose --rig RIG.blend start=IDLE.blend end=HOLD.blend
   --out POSES.json [--prefix P]`. It inverts the retarget's bone map and rest alignment and fails above 3 deg on
   any mapped bone's direction. It moves the root so the lower toe stands at Kimodo's toe height (`--toe-y`,
   0.015 m). Regenerate the poses whenever a source clip is re-baked.
3. Generate: `python3 <skill>/scripts/kimodo_motion.py generate --prompt "..." --frames F --seeds 1,2,3,4 --start
   POSES.json:start --end POSES.json:end --out DIR --name k1`. Defaults:
   - each key is held 3 frames (`--hold`): a single key let the take leave a still pose at full speed;
   - hands and feet keep their turn (`end-effector`; `--no-effectors` turns it off): positions alone left the
     hands 24-39 deg off;
   - the model's residual on its keys (about 19 mm mean, up to about 5 cm at finger ends) is eased out over 0.3 s
     (`--post`) as an offset, not a blend toward the static key (that moved joints 14-20 cm mid-motion). The
     model's own take stays in `raw/`.
4. Numeric gates, per take, in `keypose_error.json`:
   - the model's own take: mean joint error at most 30 mm on every key frame (`check DIR/k1_s1 --model` re-runs it);
   - after post: at most 5 mm on any joint (`check DIR/k1_s1` re-runs it);
   - known-bad: the same prompt and `F` without `--start/--end` (`--name k1n --seeds 1`) must FAIL
     `check DIR/k1n_s1 --model --constraints DIR/k1_s1/constraints.json` (measured: 79-289 mm). If it passes, the
     gate is broken: stop.
5. Sheets for a fresh-context reviewer or the user, never the agent that generated the takes:
   - phases: `sheet DIR/k1_s* DIR/k1_s1/raw DIR/k1n_s1 --keys DIR/k1_s1/constraints.json --out phases.png`;
   - every frame of both junctions: `--span 0:10` and `--span F-11:F-1` (75 frames: `64:74`).
   Ask for: start and end on the grey keys, pops where a hold releases, and whether the motion reads as the prompt.
   Drop takes that do something else (a seed that does the end action first keeps doing it). Take at most two
   rounds of new seeds or prompts; after that, ask the user. Mark the chosen take in `provenance.json` (`used_as`).
6. Retarget the chosen take: `"$BLENDER" -b RIG.blend --factory-startup --python-exit-code 1 --python
   <skill>/scripts/kimodo_retarget.py -- retarget --clip NAME=DIR/k1_s3 --out CLIPS.glb --report report.json
   [--prefix P]`. Every mapped bone's world turn is copied and only the hips move. Above 3 deg on any bone's
   direction it writes the report and no GLB. Fingers, props and contact fixes belong to the consumer project.
   `stats` gives the right hand's closest approach to the hip, for draw or reach clips.

## Boundaries

- Write takes into new dirs (`generate` refuses existing ones). Keep `provenance.json` (seed, command, keys) for
  AI-content disclosure. Models, licences and machine paths stay outside the skill.
- Where a hold releases, the residual offset can add a one-frame step of about 2 cm. Measure the largest per-frame
  joint step in the junction strips against `raw/` and report it. Do not hide it.

## Stop Conditions

- `kmd-generate` lacks `--constraints` (unpatched build) or a model file is missing: stop and report.
- `keypose` or `retarget` fails its direction gate, or reports missing bones: the rig's names, prefix or rest differ
  from the map. Stop; do not loosen the 3 deg tolerance.
- The known-bad passes the model gate, every take fails it, or all takes are rejected after two rounds: report the
  numbers and sheets to the user.

## Output Contract

Skill: kimodo-motion - output below

| Take | Model mean / max (mm) | After post max (mm) | Post move (mm) | Hold-release step vs raw (mm/frame) | Content verdict | Use |
| --- | --- | --- | --- | --- | --- | --- |

Followed by: the poses file, the take dirs, the known-bad result, the sheet paths, the reviewer's verdict, and the
retarget report (worst direction per clip) when baked.
