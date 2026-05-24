# T-001 — Repository scaffolding

**Epic:** 1 — Foundation
**Feature:** 1.1 — Repository scaffolding
**Status:** todo
**Dependencies:** none

## Goal

Create the canonical folder structure described in [architecture.md](../architecture.md) and stand up the minimal files every later task assumes exists.

## Deliverables

- `.skill_kit/skills/` (empty, with `.gitkeep`)
- `.skill_kit/agents/` (empty, with `.gitkeep`)
- `.skill_kit/conventions/` (empty, with `.gitkeep`)
- `.ai/` (already exists; ensure `.gitkeep` if empty)
- `.docs/tasks/` (this folder; created by this task suite)
- `.gitignore` (sensible defaults for the repo type)
- `LICENSE` (license file — MIT or whatever the maintainer chooses; confirm at task start)
- `README.md` shell (real content lands in T-005)

## Acceptance criteria

- All folders above exist and are tracked by git.
- `git status` is clean after committing the scaffolding.
- No deliverable asset files exist yet under `.skill_kit/skills`, `.skill_kit/agents`, or `.skill_kit/conventions` — only `.gitkeep`s.
- README.md exists as a minimal placeholder with the project name and a one-line description (full adoption guide lands in T-005).

## Notes

- Do not author any skill, agent, or convention content in this task.
- Confirm with the maintainer which license to use before committing `LICENSE`.
