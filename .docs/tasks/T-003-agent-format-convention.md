# T-003 — `agent-format` convention

**Epic:** 1 — Foundation
**Feature:** 1.3 — `agent-format` convention
**Status:** todo
**Dependencies:** T-001

## Goal

Author the authoritative specification for what a valid `AGENT.md` looks like, so [T-010](T-010-code-reviewer-agent.md) and [T-013](T-013-provider-adapter-agent.md) can be authored against a stable contract.

## Deliverables

- `.collection/conventions/agent-format.md`

## Content requirements

The convention document must specify:

- **Frontmatter:** required fields (`name`, `description`, `when_to_use`, `when_not_to_use`, `status`) and optional fields (e.g., `tools`, `targets`) with examples.
- **Body structure:** required sections (Purpose, When to use, When NOT to use, Inputs/Outputs, Behavior, Example).
- **Boundary rules:**
  - Agents must be specialized; they are not a default execution unit for ordinary tasks.
  - Agents must not duplicate a skill's role; if the work fits a skill, it should be a skill.
  - Cross-reference [skill-format.md](T-002-skill-format-convention.md) for the line between the two.
- **File naming and folder placement:** one folder per agent at `.collection/agents/<kebab-name>/AGENT.md`.
- **Minimal example.**

## Acceptance criteria

- Document is self-contained.
- Both v0.1 agents ([T-010], [T-013]) can be authored against this convention without ambiguity.
- `when_not_to_use` is required and enforced; reviewers can fail an agent that omits it.
- The convention explicitly addresses the skill-vs-agent boundary so the type is not chosen by default.

## Notes

- Cross-link with [skill-format.md](T-002-skill-format-convention.md); do not restate rules.
- Keep terminology aligned with the Agent Manifesto framework — reference `.manifesto/` instead of redefining roles.
