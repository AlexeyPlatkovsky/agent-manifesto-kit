---
name: task-complete
description: Produces the required closure table after non-trivial routed work completes validation, review, and documentation gates.
---

# Task Complete

## Purpose

Close non-trivial routed work by reporting what actually happened and confirming required visible artifacts exist.

## Template Reference

This skill follows `.ai/docs/skill-template.md`.

## Scope

- Use as the final step for non-trivial routed work after validation, review, and documentation maintenance gates are complete or explicitly skipped.
- Skip trivial direct work.
- Skip work that did not go through routed execution.
- Report closure as blocked when a required planned output artifact is missing.

## Procedure

1. Review the manager plan.
2. Confirm every planned routed handoff has its expected visible output artifact.
3. For every planned agent handoff, confirm the agent was run as a spawned subagent when subagent tooling was available, or that an explicit fallback reason was recorded.
4. Include every executed, skipped, blocked, or changed planned step.
5. If a required artifact, spawned subagent id, or fallback reason is missing, report closure as blocked and name the missing evidence.

## Output Contract

Emit:

`Skill: task-complete - output below`

Then provide exactly this three-column table:

| Step | Skill / Agent | Comment |
|------|---------------|---------|

Every planned routed handoff must appear as a row, including steps that were blocked before execution.

For planned routed handoffs, `Comment` must reference the visible output artifact label or transcript location.

For planned agent handoffs, `Comment` must also reference the spawned subagent id or handle when tooling was available, or the explicit fallback reason when unavailable.

Skipped steps must always include a reason in `Comment`.

If closure is blocked, use `Comment` to state `Blocked:` followed by the missing artifact, missing spawned subagent evidence, missing fallback reason, missing plan item, or unresolved closure blocker.

Do not add columns or rename columns.
