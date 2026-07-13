---
name: sdd-feature-author
description: Plans and creates one Taskpilot feature item after gap discovery, with separate DoR/DoD fields and real Taskpilot child tasks.
---

## Scope

- Create or revise exactly one Taskpilot item with `type: feature` in project `amk`.
- Keep Description concise: problem/value, scope, non-goals, stable feature/requirement
  references, and links only.
- Store readiness in `dor`, completion/acceptance and tests in `dod`, and implementation work
  as child Taskpilot `task` items using `parent_id`.
- Keep progress updates, execution evidence, and new decisions in Taskpilot comments.
- Do not create or edit `docs/features/`; Taskpilot is the only feature-tracking source.

## Required Environment

- A valid `.taskpilot/project.yaml` for project `amk`.
- The `taskpilot` CLI available and passing `taskpilot --json validate`.
- Taskpilot installation/reference: `npm install -g @alexey_platkovsky/taskpilot` and
  `https://www.npmjs.com/package/@alexey_platkovsky/taskpilot`.
- The local SDD convention at `.claude/conventions/sdd-doc-set.md`.

## Inputs

- Feature intent and short name.
- The `idea.md` scope item or `roadmap.md` entry the feature serves.
- Mode: `new` or `revise`.
- Explicit approval for creating a new Taskpilot item when no suitable item exists.
- A discovery record showing inspected sources, resolved gaps/edge cases, and the user's
  confirmation of the resulting decision summary.

## Procedure

Apply the Stop Conditions throughout; halt immediately when any is met.

1. Validate the Taskpilot workspace and inspect active items for a suitable existing feature.
2. Inspect the current code, docs, and Taskpilot records. Build a gap matrix covering intent,
   scope, requirements, non-goals, dependencies, edge/error/data/permission cases, DoR, DoD,
   and validation. Do not create or revise a feature while material gaps remain.
3. Require the prior brainstorm artifact when any material decision was unresolved. It must
   show one-question-at-a-time resolution and the user's confirmation of the decision summary.
   If it is absent or incomplete, stop; do not infer confirmation from a broad feature request.
4. In `new` mode, create the next Taskpilot `feature` item only after discovery is complete,
   the decision summary is confirmed, and creation is approved. In `revise` mode, preserve the
   existing Taskpilot item ID.
5. Write the concise Description, then populate separate non-empty `dor` and `dod` lists.
   Include tests and verification checks in `dod` when appropriate; never put these lists in
   Description.
6. Create one Taskpilot `task` child for every implementation task, each with its stable
   `F<NNN>-T<n>` identifier, concrete scope, and `parent_id` set to the feature. Do not use a
   prose task table as a substitute.
7. Add progress or verification evidence as a Taskpilot comment; do not duplicate it in docs.
8. Relate the feature item to the relevant parent or companion item only when the dependency
   is explicit.
9. Validate Taskpilot after every create, update, relationship, or comment operation, and
   inspect the final JSON/YAML to confirm Description, DoR, DoD, and child-task ownership.

## Stop Conditions

- Stop if Taskpilot validation reports errors.
- Stop if the feature cannot trace up to an `idea.md` or `roadmap.md` item.
- Stop if any material gap, edge case, or implementation decision is unresolved and the user
  has not confirmed the proposed resolution.
- Stop if `dor` or `dod` cannot be populated as separate structured fields.
- Stop if a planned implementation task cannot be created as a Taskpilot child `task`.
- Stop if Description contains a full DoR, DoD, test plan, or prose-only task breakdown.
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
| DoR | Count and confirmation status |
| DoD | Count and confirmation status, including tests where applicable |
| Child tasks | Count and canonical Taskpilot IDs with `parent_id` validation |
| Scenarios | Count and IDs |
| Traceability gaps | Requirements without a task or scenario, or `none` |
| Files changed | `.taskpilot/` paths, or `none` |
| Validation | Command and pass/fail status |
| Blockers | Unresolved issues, or `none` |
