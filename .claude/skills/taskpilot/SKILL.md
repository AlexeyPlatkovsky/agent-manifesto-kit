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
- Use Taskpilot `feature` items as the sole canonical record for feature intent, readiness,
  completion, child tasks, status, and verification evidence in this project.
- Do not create or maintain parallel feature records under `docs/features/`.
- Prepare branch-name task segments from Taskpilot IDs.
- Use JSON output for reads and changes whenever possible.
- Route Git preflight and all branch, commit, and push operations through the project-local
  `.claude/skills/work-with-git/SKILL.md`; do not perform Git operations ad hoc in this skill.
- Do not replace the root routing gate or decide whether a task is trivial.

## Branch Task Segment

- Taskpilot's canonical item ID is the source of truth.
- For branch names, convert the canonical item ID to lowercase and zero-pad the numeric suffix to three digits.
- Example: Taskpilot item `amk-1` becomes branch task segment `amk-001`.
- New feature branches use `feat/<task-segment>-<slug>` and bug branches use
  `fix/<task-segment>-<slug>`, for example `feat/amk-001-add-new-bundle` or
  `fix/amk-002-fix-adopt-cli-adaptation-handoff`.

## Git Workflow Handoff

- Before implementing a new feature or bug fix, the manager must route through
  `work-with-git`.
- Taskpilot supplies the canonical item ID and type for branch naming; `work-with-git` decides
  whether the current branch is related and owns any approved branch operation.
- Taskpilot item creation, update, relationship, comment, and validation operations remain here;
  Git branch, commit, and push operations do not.

## Feature Records

- Create feature records with `--type feature` in project `amk`.
- Keep `description` concise: problem/value, scope, non-goals, stable feature/requirement
  references, and links only. Do not place DoR, DoD, tests, or a task breakdown there.
- Store readiness conditions in the feature's `dor` list.
- Store observable acceptance/completion conditions in the feature's `dod` list; tests and
  verification checks may be included there.
- Create one separate Taskpilot `task` item for every implementation task, with the feature
  item as its `parent_id`. Put the stable `F<NNN>-T<n>` identifier on the child task, not only
  in the feature description. Child task status is authoritative for that work unit.
- Store stable scenario IDs and the acceptance mapping in `dod` or child-task descriptions as
  appropriate; keep execution evidence and later decisions in Taskpilot comments.
- Relate feature items to originating or enabling work items when the dependency is explicit.

The installed CLI may not expose `--dor` or `--dod` flags. Inspect the actual Taskpilot
schema and, when the fields are supported but omitted from the CLI, update the canonical
`.taskpilot/items/<id>.yaml` record through a schema-valid structured edit, preserve its
identity/history, and run `taskpilot --json validate` immediately. If neither the CLI nor
that canonical structured path is available, stop and report the tooling gap; never flatten
the fields or child tasks into Description.

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
   For feature breakdowns, create each child task with `--type task` and `--parent FEATURE_ID`,
   then verify the child's `parent_id` in JSON output. Do not represent the breakdown only as
   `F<NNN>-T<n>` prose.
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
- Stop if a feature has an empty/missing `dor` or `dod` when the workflow requires them.
- Stop if a feature's implementation tasks are prose-only, lack child Taskpilot items, or have
  the wrong parent/type.
- Stop if a writer would place DoR, DoD, tests, or tasks in Description because structured
  fields or child relationships are inconvenient.
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
