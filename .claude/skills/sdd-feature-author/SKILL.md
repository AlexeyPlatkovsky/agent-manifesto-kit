---
name: sdd-feature-author
description: Creates or updates one Taskpilot feature item with stable requirements, acceptance criteria, tasks, scenarios, and progress links for this project.
---

## Scope

- Create or revise exactly one Taskpilot item with `type: feature` in project `amk`.
- Keep the feature summary, requirements, acceptance criteria, tasks, scenarios,
  constraints, and out-of-scope in the item description.
- Keep progress updates and verification evidence in Taskpilot comments.
- Do not create or edit `docs/features/`; Taskpilot is the only feature-tracking source.

## Required Environment

- A valid `.taskpilot/project.yaml` for project `amk`.
- The `taskpilot` CLI available and passing `taskpilot --json validate`.
- The local SDD convention at `.claude/conventions/sdd-doc-set.md`.

## Inputs

- Feature intent and short name.
- The `idea.md` scope item or `roadmap.md` entry the feature serves.
- Mode: `new` or `revise`.
- Explicit approval for creating a new Taskpilot item when no suitable item exists.

## Procedure

Apply the Stop Conditions throughout; halt immediately when any is met.

1. Validate the Taskpilot workspace and inspect active items for a suitable existing feature.
2. In `new` mode, create the next Taskpilot `feature` item only after creation is approved.
   In `revise` mode, preserve the existing Taskpilot item ID.
3. Write or update the item description with stable `F<NNN>-R<n>`, `F<NNN>-T<n>`, and
   `F<NNN>-S<n>` records, observable acceptance criteria, constraints, and out-of-scope.
4. Add progress or verification evidence as a Taskpilot comment; do not duplicate it in docs.
5. Relate the feature item to the relevant parent or companion item only when the dependency
   is explicit.
6. Validate Taskpilot after every create, update, relationship, or comment operation.

## Stop Conditions

- Stop if Taskpilot validation reports errors.
- Stop if the feature cannot trace up to an `idea.md` or `roadmap.md` item.
- Stop if a requirement, task, or scenario is missing a stable link.
- Stop if two existing items are plausible matches; present the options instead of guessing.
- Stop before creating a new item without explicit approval.

## Output Contract

Emit:

`Skill: sdd-feature-author - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed`, `blocked`, or `skipped` |
| Item | Canonical Taskpilot ID and title |
| Feature ID | `F<NNN>` and short name |
| Requirements | Count and IDs |
| Tasks | Count and IDs |
| Scenarios | Count and IDs |
| Traceability gaps | Requirements without a task or scenario, or `none` |
| Files changed | `.taskpilot/` paths, or `none` |
| Validation | Command and pass/fail status |
| Blockers | Unresolved issues, or `none` |
