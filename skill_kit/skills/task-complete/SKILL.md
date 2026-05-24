---
name: task-complete
description: Produces the required closure table for non-trivial routed work. Use as the final step after all validation, review, and documentation maintenance gates are done.
---

# Task Complete

## Purpose

Close non-trivial routed work by reporting what actually happened and confirming required visible artifacts exist.

## When To Use

Use as the final step for non-trivial routed work after validation, review, and documentation maintenance gates are complete or explicitly skipped with reasons.

## When Not To Use

- Trivial direct work.
- Work that did not go through routed execution.
- When a required planned output artifact is missing — report closure as blocked instead.

## Procedure

1. Review the execution plan.
2. Confirm every planned step has its expected visible output artifact.
3. Include every executed, skipped, blocked, or changed step in the closure table.
4. If a required artifact is missing, report closure as blocked and name the missing artifact.

## Output Contract

Emit:

`Skill: task-complete - output below`

Then provide exactly this three-column table:

| Step | Skill / Agent | Comment |
| --- | --- | --- |

Use `Comment` when:
- a step was skipped — explain why
- execution deviated from the plan — note the deviation
- the user should notice something incomplete or unusual
- for planned routed handoffs, reference the step's visible output artifact label (e.g., `"Skill: review-code - output above"`)

Leave `Comment` empty for steps that executed as planned with no noteworthy output.

Do not add columns or rename columns.
