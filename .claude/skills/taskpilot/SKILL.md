---
name: taskpilot
description: Manages local Taskpilot work items for this repository and prepares Taskpilot-backed branch names when non-trivial project work needs a tracked task.
---

# Taskpilot

## Prerequisites

- Install Taskpilot with `npm install -g @alexey_platkovsky/taskpilot`.
- Verify with `taskpilot --help`.
- This repository is initialized with `taskpilot init . --key amk --name "Agent Manifesto Kit"`.
- Taskpilot docs: https://www.npmjs.com/package/@alexey_platkovsky/taskpilot

## Scope

- Inspect, create, update, link, comment on, and soft-delete Taskpilot items in `.taskpilot/`.
- Prepare branch-name task segments from Taskpilot IDs.
- Use JSON output for reads and changes whenever possible.
- Do not manage Git branches directly; branch creation remains owned by the Git workflow or caller.
- Do not replace the root routing gate or decide whether a task is trivial.

## Branch Task Segment

- Taskpilot's canonical item ID is the source of truth.
- For branch names, convert the canonical item ID to lowercase and zero-pad the numeric suffix to three digits.
- Example: Taskpilot item `amk-1` becomes branch task segment `amk-001`.
- New non-trivial feature/work branches use `feature/<task-segment>-<slug>`, for example `feature/amk-001-add-new-bundle`.

## Procedure

Before and during these steps, apply Stop Conditions immediately; when one matches, halt and report the blocker.

1. Verify the workspace:
   ```bash
   taskpilot --json validate
   ```
2. For task-backed branch work, list active items before creating a new one:
   ```bash
   taskpilot --json item list --project amk
   ```
   Include `--include-deleted` only when recovering or auditing deleted work.
3. If a suitable item exists, show it and use its canonical ID:
   ```bash
   taskpilot --json item show amk-1
   ```
4. If no suitable item exists and the caller has approved creation, create one:
   ```bash
   taskpilot --json item create --title "<title>" --type task --status backlog --created-by codex
   ```
   Use `--description`, `--priority`, `--parent`, and repeated `--tag` when they are known and useful.
5. Update item fields with:
   ```bash
   taskpilot --json item update amk-1 --status in_progress
   ```
6. Add durable progress context with:
   ```bash
   taskpilot --json item comment amk-1 "Short factual update."
   ```
7. Manage relationships only when the dependency is explicit:
   ```bash
   taskpilot --json item parent CHILD_ID PARENT_ID
   taskpilot --json item blocks BLOCKER_ID TARGET_ID
   taskpilot --json item relates SOURCE_ID TARGET_ID
   ```
8. For deletion, require explicit user confirmation naming the item ID and title. After confirmation, soft-delete by setting status to `deleted`:
   ```bash
   taskpilot --json item update amk-1 --status deleted
   ```
9. Validate after any create, update, relationship change, comment, or soft-delete:
   ```bash
   taskpilot --json validate
   ```

## Stop Conditions

- Stop if `taskpilot --json validate` reports errors.
- Stop if `.taskpilot/project.yaml` is missing or the project key is not `amk`.
- Stop if item creation, update, relationship changes, or deletion were not explicitly requested or approved.
- Stop before deletion unless the user confirms the exact item ID and title.
- Stop if two or more existing items are plausible matches for branch work; present the options instead of guessing.

## Output Contract

Emit:

`Skill: taskpilot - output below`

Then include:

| Field | Value |
| --- | --- |
| Action | inspect / create / update / comment / link / soft-delete / branch-segment |
| Item | canonical Taskpilot ID and title, or `none` |
| Branch segment | lowercase zero-padded segment, or `not applicable` |
| Files changed | `.taskpilot/` paths changed, or `none` |
| Validation | pass / fail / skipped, with command |
| Blockers | none, or concrete blocker |
