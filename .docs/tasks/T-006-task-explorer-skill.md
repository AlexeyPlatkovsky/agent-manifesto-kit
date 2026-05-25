# T-006 — `task-explorer` skill

**Epic:** 2 — Skills
**Feature:** 2.1 — `task-explorer` skill
**Status:** todo
**Dependencies:** T-002

## Goal

Author the `task-explorer` skill: investigates a task before implementation and produces a grounded implementation plan. This is the kit's flagship skill and the first proof of [skill-format.md](T-002-skill-format-convention.md).

## Deliverables

- `.collection/skills/task-explorer/SKILL.md`

## Behavior outline (to encode in the skill)

The skill, when triggered, should guide the assistant to:

1. Identify the request and any ambiguities worth resolving up front.
2. Locate relevant files, prior decisions, and existing patterns in the project.
3. Surface constraints (framework rules, project conventions, performance, security).
4. Produce a written implementation plan: scope, steps, risks, open questions, files to touch.
5. Stop before implementation; the plan is the artifact.

## Acceptance criteria

- Conforms to [skill-format.md](T-002-skill-format-convention.md): frontmatter, sections, no orchestration, no agent delegation.
- The skill is **atomic** — it produces a plan and stops. It does not implement, it does not call other skills.
- Includes a concrete usage example in the body (one minimal scenario).
- `triggers` frontmatter field lists situations where the skill should fire (e.g., before non-trivial implementation work, on user request).
- The skill works in isolation: a consumer who installs only this skill (and nothing else from the kit) gets value.

## Notes

- This skill is the highest-priority asset; prioritize quality and clarity over breadth.
- Usage examples lands in this file directly (per [T-015](T-015-per-asset-usage-examples.md) policy).
