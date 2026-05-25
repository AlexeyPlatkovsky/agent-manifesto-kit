# T-002 — `skill-format` convention

**Epic:** 1 — Foundation
**Feature:** 1.2 — `skill-format` convention
**Status:** todo
**Dependencies:** T-001

## Goal

Author the authoritative specification for what a valid `SKILL.md` looks like in this kit, so every later skill task ([T-006], [T-007], [T-008]) and the catalog ([T-004]) can reference one source of truth.

## Deliverables

- `.collection/conventions/skill-format.md`

## Content requirements

The convention document must specify:

- **Frontmatter:** required fields (`name`, `description`, `triggers`, `status`) and optional fields, with allowed values and examples.
- **Body structure:** required sections (Purpose, When to use, When NOT to use, Inputs/Outputs, Steps, Example) with brief guidance on what each contains.
- **Boundary rules:** what skills must NOT contain (routing/orchestration, calls to other skills, agent delegation logic, framework protocol restatements).
- **File naming and folder placement:** one folder per skill at `.collection/skills/<kebab-name>/SKILL.md`.
- **Minimal example:** a small but complete sample skill demonstrating the format.

## Acceptance criteria

- Document is self-contained; reading it alone is enough to author a valid skill.
- All three v0.1 skills ([T-006], [T-007], [T-008]) can be authored against this convention without ambiguity.
- The boundary rules explicitly disallow orchestration so a reviewer can fail a skill that drifts into pipeline territory.
- The convention does not duplicate any rule that belongs in [agent-format.md](T-003-agent-format-convention.md); cross-reference instead.

## Notes

- Keep the convention short. Long conventions are not read.
- Pair-review this with [T-003](T-003-agent-format-convention.md) to keep the two conventions consistent in style.

[T-006]: T-006-task-explorer-skill.md
[T-007]: T-007-docs-sync-skill.md
[T-008]: T-008-test-review-skill.md
[T-004]: T-004-catalog-schema.md
