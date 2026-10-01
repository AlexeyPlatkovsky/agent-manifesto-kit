# Blender 3D

A portable Blender asset workflow with effort matched to the task. Use the same bundle for a
small prop, a reference-matched game asset, or a complex model with animation and engine checks.

## Profiles

| Profile | Typical work | Sequence | Independent review | Repair ceiling |
| --- | --- | --- | --- | --- |
| Quick | Simple prop, prototype, material/origin edit, isolated repair | Build → relevant technical checks → affected views → delivery | When requested or materially uncertain | 1 |
| Standard | Reference matching, modular asset, ordinary game-ready delivery | Proportions → build → comparison if applicable → technical checks → delivery | Required when requested or identity/acceptance remains uncertain | 2 |
| Production | Strict fidelity, complex assembly, critical deformation, dependent deliverables | Acceptance/blockout checkpoint → refine → technical gates → review → delivery | One fresh-context reviewer required | 3 |

Each row permits focused fixes within its ceiling, followed by affected checks. Missing required
checks or review blocks acceptance. Optional taste changes do not force more rounds. Animation,
retargeting and engine export add their own criteria to any profile; they do not restart modeling.
The calling agent chooses the smallest suitable profile and records why. Project budgets may
set an explicit initial ceiling; later increases require a user decision.

## Contents

| Item | Purpose |
| --- | --- |
| `blender-asset` skill | Entry capability for a build or focused revision, with or without a reference |
| `blender-asset/workflows/asset.yml` | Declarative profile selection, stage sequencing, review and completion rules |
| `blender-asset/scripts/task_state.py` | Compact task handoff, file-dependent evidence and repair reservations |
| `blender-asset/scripts/record_run.py` | Per-phase usage journal with parent/child identities and unknown-value coverage |
| `blender-reference-model` skill and scripts | Measurements, matched renders, identity details and mesh diagnostics |
| `blender-mocap-retarget` skill and scripts | Appearance preservation, source-motion comparison, motion and export checks |
| `visual-reviewer` agent | Read-only image review with at most five ranked findings |

The complete bundle is the supported installation unit. The YAML is read by the calling agent;
it is not an executable orchestrator. No always-on hooks, automatic teams or fixed model presets
are installed. Machine paths, model/effort preferences, task state and usage logs belong in the
consumer project, outside the synced skill directories.

## Install and requirements

```bash
agentkit sync blender-3d --provider claude,codex
```

Sync copies skills, their nested workflow/scripts and the agent. It preserves local edits under
the normal sync conflict rules. Use `agentkit adopt blender-3d --provider <provider>` for a
one-off copy intended for local adaptation. No CLI changes are needed for these profiles.

- Install [Blender](https://www.blender.org/download/), verify `blender --version`.
  Current fixture validation uses Blender 5.2.1 LTS; other versions need project verification.
- Install [Python 3](https://www.python.org/downloads/), verify `python3 --version`.
  State and usage helpers use only its standard library. Image tools need
  `python3 -m pip install Pillow numpy`; verify `python3 -c "import PIL, numpy"`.
- For a Godot target, install [Godot 4](https://godotengine.org/download/) and verify
  `godot --version`; `GODOT` may hold its executable path.
- A required visual reviewer needs image viewing and independent-agent support in its session.
  When unavailable, mark that gate `not_tested` and report partial delivery.

## Start and resume

Ask the agent to use `blender-asset`, for example: “Quick: create a low-poly crate, 1 m wide,
under 400 triangles; deliver the editable blend and a front/three-quarter preview.” A strict
reference character can request Production with its views, identity priorities and export needs.

The coordinator records a task contract and required evidence before building. These examples
use Claude paths; Codex uses `.agents/skills` instead. Paths supplied to `task_state.py` resolve
relative to the state file's directory, independent of the current shell directory.

```bash
python3 .claude/skills/blender-asset/scripts/task_state.py init \
  --state work/crate/task.json --profile quick --artifact crate.blend \
  --acceptance brief.json --require geometry --require preview
python3 .claude/skills/blender-asset/scripts/task_state.py evidence \
  --state work/crate/task.json --name geometry --result pass \
  --depends crate.blend --depends build.py --report mesh.json
python3 .claude/skills/blender-asset/scripts/task_state.py status \
  --state work/crate/task.json --strict
```

The brief and evidence files must exist when they are registered. Repeat evidence registration
for `preview` with its actual dependencies and image report; until then, strict status fails.
An evidence record is an assertion of a performed check, not an automatic visual judgment.
Hashes detect changed/missing declared files, not undeclared dependencies: include inputs,
builder, reference, render settings and export as appropriate. Unchanged independent evidence
can be reused. A coarse dependency such as the whole `.blend` conservatively invalidates all
checks registered against it when it changes.

Before a correction, reserve a round with `repair --state ... --reason "fix latch position"`.
Use `handoff --state ... --phase build --summary ... --next ... --ref ...` to leave compact
context for a new fix session; use `--phase fix` after that stage. Resume with the authoritative
asset, saved builder/edit script, criteria and unresolved findings. A lack of progress or an
exhausted ceiling ends repairs with remaining defects disclosed; do not reset state to evade it.
The state helper records reservations and evidence; the coordinator enforces the workflow.

## Measure accepted-task cost

```bash
python3 .claude/skills/blender-asset/scripts/record_run.py record \
  --log work/crate/usage.jsonl --event-id create-1 --phase create \
  --provider codex --model project-selected-model --input-tokens 1200 \
  --output-tokens 400 --render-count 2 --render-seconds 4.5 --acceptance pass
python3 .claude/skills/blender-asset/scripts/record_run.py summary \
  --log work/crate/usage.jsonl
```

Record create, review and fix calls separately, with `--parent-id` for child calls. Each row
contains only that call's own usage; never record an inclusive parent total plus the same child
usage. Token categories are disjoint: `--input-tokens` excludes cache-read/write tokens;
normalize provider totals before recording them. Summed call durations are not wall-clock
duration when calls overlap. Unknown metrics remain null and summaries expose incomplete
coverage. Duplicate event
IDs cannot double count the same call. Render time, token/API usage and any supplied dollar
estimate measure different costs; `--advisory-dollars` requires `--advisory-source`.
These helpers neither read billing automatically nor enforce a live spending limit. The
coordinator writes state and usage sequentially; concurrent writers are not supported.

Compare workflows on comparable tasks that reached the same acceptance criteria, including
failed attempts, fixes and reviews. A create/fix split and lower effort are candidates to
measure, not a promised saving. Model choices remain in project configuration.

## Technical acceptance

`check_motion.py` reports scope and coverage. Optional `--strict` requires at least one explicit
threshold: `--max-ground-penetration-mm`, `--max-planted-slide-mm-per-frame`,
`--max-extra-overlap-tris`, `--max-loop-rotation-deg`. Requested checks with no coverage fail
strict acceptance. Name relevant feet/pairs and the frame range; unrequested checks are diagnostics.
Use `blender -b asset.blend --python-exit-code 1 --python <script> -- <args>` for reliable failure propagation.

For exports, `verify_gltf.py file.glb --expect-clips Walk,Run --exact-clips --require-mesh
--require-skin --require-rig` checks original clip names including extras and re-imported structure.
Invoke it through Blender as above. For a static export, `--exact-clips` without `--expect-clips`
requires an empty clip set. Require only the structure the task actually needs.

## Provenance and limits

The original modeling and retarget tools came from measured reference-character sessions.
The 1.5.0 workflow separates that demanding use case from simpler tasks, based on a two-week
Claude/Codex session audit. The audit did not establish that two medium sessions match one
large session at half the price. Silhouette scores, technical checks and sampled images each
cover different criteria; none is a universal quality certificate.
