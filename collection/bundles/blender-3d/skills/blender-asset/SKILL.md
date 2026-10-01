---
name: blender-asset
description: Build or revise a Blender asset from a brief, including simple props, prototypes and focused fixes without a reference sheet. Use as the blender-3d bundle entry capability; task complexity and optional reference, motion or export work are coordinated by its accompanying asset workflow.
---

# Blender Asset

## Scope

Produce one reproducible asset build or a targeted revision from a supplied task contract.
Supports a written brief without an image, an existing asset, or a measured reference.
Cross-skill sequencing, profile selection, reviews and repair limits belong to
[`workflows/asset.yml`](workflows/asset.yml), interpreted by the calling agent or manager;
it is an instruction workflow, not an executable runner. Direct invocation without a contract
returns the missing contract fields to that coordinator before modifying an asset.

## Prerequisites

- Install the complete `blender-3d` bundle; its sibling skills and workflow are required context.
- Install [Blender](https://www.blender.org/download/); verify `blender --version`.
  Store its executable path in consumer-project configuration if it is not on `PATH`.
- Install [Python 3](https://www.python.org/downloads/); verify `python3 --version`.
  The state and usage helpers use only the standard library.
- Reference-image tools additionally need Pillow and numpy; see the reference skill.

## Inputs

A task contract supplies the brief, chosen profile, authoritative input paths, output paths,
acceptance criteria, required views/checks and applicable tolerances. Include units, axes,
origin, dimensions, polygon/material constraints and target engine only when relevant.
Identify editable source versus derived outputs. A revision also names the changed region,
existing failures, allowed changes and previous evidence to reuse.

## Procedure

Apply Stop Conditions immediately during every step; return the blocked work and evidence gaps.

1. Inspect the named inputs and existing scene before writing. Use existing project conventions;
   otherwise record reasonable units, axes and origin defaults in the task contract. Do not
   impose character conventions on props or architectural assets.
2. Make the smallest persisted Blender Python builder or edit script that produces the requested
   change. Preserve user-authored geometry, materials and names outside that change. Save to
   the agreed output; never overwrite an authoritative hand-edited `.blend` by rebuilding it.
   Build into a new file and reconcile when script and scene disagree.
3. For a new asset, establish scale and primary forms before details. For a narrow repair,
   edit the affected region; do not restart the whole asset or regenerate unchanged views.
4. Run the contract's relevant technical checks and render the affected views at the intended
   presentation or gameplay size. Record checks as `pass`, `fail` or `not_tested`, with scope,
   sample coverage and artifact paths. Missing tools or evidence cannot count as a pass.
5. Save the editable `.blend`, its builder/edit script and requested exports. Return the
   artifact paths, evidence, remaining defects and actual changes for the coordinator's next
   gate. Stop this invocation after one build or repair stage.

## State and Usage Helpers

Resolve scripts relative to this skill directory, not the shell working directory.
`python3 scripts/task_state.py --help` describes compact task state, file-dependent evidence
and bounded repair reservations. `python3 scripts/record_run.py --help` describes per-phase
usage records. Store their output in a consumer task directory outside synced skill files.
They do not launch agents, render, collect billing automatically or enforce a live money cap.

## Stop Conditions

- An essential reference/input is missing, acceptance criteria conflict, or an edit would
  overwrite authoritative work: return the concrete blocker without changing that work.
- A required check cannot run: record `not_tested` and return the missing capability.
- The coordinator has not reserved a permitted repair round: do not start another repair.

## Output Contract

`Skill: blender-asset - output below`

Report: profile and stage; changed artifacts; checks with status and scope; evidence paths;
known defects or blockers; usage-record path (or unavailable metrics). The asset files and
persisted script are the primary output. Never claim overall acceptance from this build stage.
