# T-007 — `docs-sync` skill

**Epic:** 2 — Skills
**Feature:** 2.2 — `docs-sync` skill
**Status:** todo
**Dependencies:** T-002

## Goal

Author the `docs-sync` skill: keeps project documentation synchronized with implementation changes.

## Deliverables

- `.claude/skills/docs-sync/SKILL.md`

## Behavior outline

When triggered (typically after non-trivial code changes), the skill should guide the assistant to:

1. Identify what changed in the codebase.
2. Find documentation that references the changed surfaces (READMEs, in-code docs, architecture notes, public API references).
3. Propose minimal documentation updates that keep docs accurate without expanding scope.
4. Flag docs that are now stale but outside the requested change's scope.

## Acceptance criteria

- Conforms to [skill-format.md](T-002-skill-format-convention.md).
- Atomic: produces doc updates only; does not modify code, does not run tests, does not orchestrate.
- `triggers` field lists the typical triggers (after a feature implementation, after refactoring a public API, on explicit user request).
- Includes a concrete usage example.
- Explicitly states it does NOT generate net-new documentation pages without user direction.

## Notes

- This skill must avoid the common failure mode of generating exhaustive doc rewrites. Keep change scope minimal.
