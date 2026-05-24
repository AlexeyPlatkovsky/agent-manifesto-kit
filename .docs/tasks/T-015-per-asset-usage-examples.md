# T-015 — Per-asset usage examples

**Epic:** 4 — Adoption
**Feature:** 4.1 — Per-asset usage examples
**Status:** todo
**Dependencies:** T-006, T-007, T-008, T-010, T-013

## Goal

Ensure every shipped asset (3 skills, 2 agents) contains a minimal, copy-pasteable usage example demonstrating its trigger and expected behavior.

## Deliverables

Edits to each of the five v0.1 assets:

- `.skill_kit/skills/task-explorer/SKILL.md`
- `.skill_kit/skills/docs-sync/SKILL.md`
- `.skill_kit/skills/test-review/SKILL.md`
- `.skill_kit/agents/code-reviewer/AGENT.md`
- `.skill_kit/agents/provider-adapter/AGENT.md`

If the example sections already exist from their original authoring tasks, this task is a quality pass: ensure each example is concrete, minimal, and actually executable in spirit.

## Acceptance criteria

- Every asset has at least one usage example in its body.
- Each example is concrete: shows a real prompt or trigger, expected behavior, expected output shape.
- Examples are minimal — one scenario each, not a tutorial.
- `provider-adapter` has at least two examples: one targeting `codex`, one targeting `ai`.
- No example depends on private context or unstated project facts.

## Notes

- If an authoring task already produced a good example, this task may be a no-op for that asset. Note that in the task notes when closing.
- This is the quality bar referenced in [idea.md § Quality Bar](../idea.md): "documented with at least one usage example".
