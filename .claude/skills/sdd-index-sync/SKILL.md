---
name: sdd-index-sync
description: Rebuilds docs/INDEX.md from the current context-document tree and its canonical Taskpilot work/feature records.
---

## Scope

- Regenerate `docs/INDEX.md` only, from the present docs tree and Taskpilot project `amk`.
- Register the main and extension docs that exist, the Taskpilot tracking pointer, and ADRs.
- Do not create or edit `docs/features/`; do not invent Taskpilot statuses or duplicate item
  descriptions in the index.

## Required Environment

This skill depends on:
- the local `sdd-doc-set` convention (context layout, ownership, tiers, and IDs);
- the `docs/INDEX.md` template under `.claude/sdd/templates/docs/`;
- a valid `.taskpilot/project.yaml` for project `amk`.

If the docs root or Taskpilot project cannot be located, report it as a blocker.

## Inputs

- The `docs/` root.
- The current Taskpilot item list for project `amk`.

## Procedure

Apply the Stop Conditions throughout; halt immediately when any is met.

1. Scan the docs root for present main and extension docs.
2. Scan `decisions/` for `ADR-*` files and read each status.
3. List canonical Taskpilot items for project `amk`; include only stable IDs and short scope
   pointers in the index. Do not duplicate Taskpilot type or status.
4. Render `INDEX.md` from the template with the context-document map, Taskpilot tracking
   pointer, and decision log.
5. Preserve human-curated "read when" descriptions and notes where they already exist.
6. Flag any stale `docs/features/` reference or missing Taskpilot item named by the index.

## Stop Conditions

- Stop if the docs root is missing or is not recognizable.
- Stop if Taskpilot validation reports errors.
- Stop if the index would need invented statuses or duplicated feature content.

## Output Contract

Emit:

`Skill: sdd-index-sync - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed`, `blocked`, or `skipped` |
| Docs registered | Count and names |
| Taskpilot items registered | IDs and scope pointers |
| ADRs registered | Count and IDs |
| Gaps flagged | Stale references or tracking gaps, or `none` |
| Blockers | Unresolved issues, or `none` |
