---
name: documentation-maintenance
description: Checks whether completed changes require documentation updates and applies narrow, accurate updates when safe. Use after non-trivial implementation or refactoring.
---

## Scope

- Keep project documentation synchronized with completed changes.
- Run after non-trivial work that changes: project behavior visible to users or developers; public interfaces, APIs, or key abstractions; commands documented in README or guides; architecture, layer responsibilities, or domain facts; documented workflows or capability contracts; established conventions or project structure.

## Safety Constraints

- Update, do not rewrite surrounding content.
- Do not add new doc sections unless the change introduces a genuinely new concept with no existing home.
- Verify that any commands, paths, or behaviors in updated docs still match the current codebase.
- Documentation records facts. Do not add behavioral rules to docs — behavioral rules belong in skills, conventions, or root contracts.
- Do not move, reorganize, or create documentation roots unless the user explicitly requested that structural change.
- Do not silently rewrite documentation to hide a code-doc contract conflict; report the conflict as blocked.

## Stop Conditions

- If the diff or executed steps cannot be identified, stop and ask the user to describe what changed before proceeding.
- If no recognized documentation roots exist, such as `docs/`, documentation directories, README files, or project-declared doc roots, stop and report — do not create documentation structure speculatively.
- Stop and report `documentation update needed but blocked` when the needed update is unclear, risky, outside the approved task scope, unsupported by an authoritative source, or would require resolving a conflict between documentation and implementation.
- Blocked reports must name the affected doc area, why the update could not be made safely, and what decision or source is needed.

## Procedure

1. Identify what changed from the actual diff or executed steps.
2. Locate the project's authoritative documentation roots (e.g., `docs/`, `README.md`, or wherever the project records its docs — check the project profile or root contract).
3. For each changed area, identify which docs reference or describe it.
4. Load only the docs that reference the changed surface — do not load unrelated docs.
5. Update only sections that are now inaccurate or incomplete.
6. If a needed update is unclear or risky, report the gap instead of guessing.
7. Before deciding no update is needed, re-check the surfaces listed in `Scope`. If none apply, report `documentation checked and no update needed`.

## Verification

Before emitting the output, verify:
- Updated documentation facts are supported by the actual diff, executed steps, or user-provided source.
- Changed commands, paths, public names, anchors, and cross-references still resolve.
- Any docs index or README affected by created, removed, renamed, or moved docs was updated.

## Output Contract

Emit:

`Skill: documentation-maintenance - output below`

Include:

| Status | Changed Surface | Docs Checked | Docs Updated | Blockers |
| --- | --- | --- | --- | --- |

Status must be one of:
- `documentation updated`
- `documentation checked and no update needed`
- `documentation update needed but blocked`

`Docs Updated` may be `none`. `Blockers` must be `none` unless status is `documentation update needed but blocked`; when blocked, it must include the decision, source, or scope approval needed.
