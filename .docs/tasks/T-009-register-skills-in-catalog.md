# T-009 — Register skills in `catalog.json`

**Epic:** 2 — Skills
**Feature:** 2.4 — Skill catalog registration
**Status:** todo
**Dependencies:** T-004, T-006, T-007, T-008

## Goal

Add catalog entries for all three v0.1 skills so they are discoverable.

## Deliverables

- Updated `catalog.json` with three new entries under `capabilities[]`: `task-explorer`, `docs-sync`, `test-review`.

## Entry requirements

Each entry must include:

- `name` (matches the skill folder)
- `type`: `"skill"`
- `path`: `"collection/skills/<name>/SKILL.md"`
- `description` (one sentence, matches the skill's frontmatter description)
- `status`: `"experimental"` (per v0.1 stability stance)
- `tags`: descriptive tags consistent across skills (e.g., `["planning", "implementation"]` for `task-explorer`)
- `targets`: `["claude", "codex", "ai"]` (each skill must be adapter-translatable to all v0.1 targets)

## Acceptance criteria

- `catalog.json` remains valid JSON.
- All three skills appear with the fields above.
- `path` values match the actual on-disk paths.
- `description` field matches the skill's frontmatter (no drift).
- Schema invariants from [T-004](T-004-catalog-schema.md) still hold.

## Notes

- If the adapter ([T-013](T-013-provider-adapter-agent.md)) cannot yet translate a given skill to a given target, leave the target out of `targets` rather than asserting support. Honesty > completeness.
