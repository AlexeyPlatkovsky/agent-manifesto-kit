# T-011 — Codex target format spec

**Epic:** 3 — Agents
**Feature:** 3.2 — Codex target format spec
**Status:** todo
**Dependencies:** T-002, T-003

## Goal

Document the `.codex/` layout, file naming, and frontmatter conventions that [T-013](T-013-provider-adapter-agent.md) (the `provider-adapter` agent) must produce when target is `codex`.

## Deliverables

- A target format specification document. Location options (decide at task start):
  - `.skill_kit/conventions/target-codex.md` — treats target specs as kit conventions
  - `.docs/targets/codex.md` — treats target specs as planning artifacts

Pick one and be consistent with [T-012](T-012-ai-agnostic-target-format.md).

## Content requirements

- **Folder structure** Codex expects (e.g., `.codex/skills/<name>/`, file name casing).
- **Frontmatter mapping:** which fields in the `.skill_kit/` source map to which Codex fields; what to do with fields that have no Codex equivalent.
- **Body adjustments:** terminology to swap (e.g., "subagent" → Codex equivalent), tooling references to rewrite, sections to drop if not applicable.
- **Concrete before/after example:** show a snippet of `.skill_kit/skills/<name>/SKILL.md` and its Codex output side by side.
- **Unsupported features:** explicit list of source features the adapter must flag rather than silently drop.

## Acceptance criteria

- Document is precise enough for the adapter agent to apply deterministically.
- Every field, folder, and casing rule in [skill-format.md](T-002-skill-format-convention.md) and [agent-format.md](T-003-agent-format-convention.md) has a documented Codex mapping (or an explicit "drop / flag" rule).
- The before/after example uses one of the v0.1 skills so this can be validated against real source assets.

## Notes

- Coordinate with [T-012](T-012-ai-agnostic-target-format.md) on document location and style.
- This spec is the contract the adapter agent enforces. If the spec changes, the adapter's behavior changes.
