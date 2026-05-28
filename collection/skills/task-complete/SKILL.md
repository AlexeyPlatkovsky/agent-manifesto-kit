---
name: task-complete
description: Produces the required closure table for non-trivial routed work after all required routed gates are complete, skipped with reasons, or blocked.
---

## Scope

- Close non-trivial routed work by reporting what actually happened and confirming required visible artifacts exist.
- Use as the final step for non-trivial routed work after all required routed gates are complete, skipped with reasons, or blocked.

## Prerequisites

Before emitting closure, confirm:
- The routed execution plan or manager artifact is available.
- Every planned routed handoff can be identified.
- Each required handoff has a visible output artifact label or transcript location.
- Required routed gates are complete, skipped with reasons, or blocked.

## Safety Constraints

- Do not reopen routing, redesign the plan, or add new execution steps during closure.
- Do not treat raw command output as a substitute for a required visible output artifact.
- Do not declare completion when required routed evidence is missing.

## Stop Conditions

Stop and report closure as blocked when:
- The routed plan cannot be found.
- A required planned step is missing from the transcript.
- A required visible output artifact is missing.
- A skipped or changed gate has no stated reason.
- Closure would require inventing, reordering, or redesigning routed steps after execution.

When blocked, still emit the required header and exact three-column table. Add a row for the blocked or missing step, and name the missing artifact or decision in `Comment`.

## Procedure

1. Review the execution plan.
2. Confirm every planned step has its expected visible output artifact.
3. Include every executed, skipped, blocked, or changed step in the closure table.
4. If a required artifact is missing, use the blocked closure behavior defined above.

## Verification

Before emitting the closure table, verify:
- The table has exactly `Step`, `Skill / Agent`, and `Comment` columns.
- No planned routed step is omitted.
- Comments identify skipped, blocked, changed, incomplete, or unusual steps.
- Required visible output artifact labels are referenced for planned routed handoffs.
- The report describes actual execution, not the idealized plan.

## Output Contract

Emit:

`Skill: task-complete - output below`

Then provide exactly this three-column table:

| Step | Skill / Agent | Comment |
| --- | --- | --- |

Every planned routed handoff must appear as a row, including steps that were blocked before execution.

For planned routed handoffs, `Comment` must reference the visible output artifact label or transcript location.

Skipped steps must always include a reason in `Comment`.

If closure is blocked, use `Comment` to state `Blocked:` followed by the missing artifact, missing plan item, or unresolved closure blocker.

Use `Comment` when:
- a step was skipped — explain why
- execution deviated from the plan — note the deviation
- the user should notice something incomplete or unusual
- for planned routed handoffs, reference the step's visible output artifact label (e.g., `"Skill: review-code - output above"`)

Leave `Comment` empty only for included non-handoff steps that executed as planned with no noteworthy output.

Do not add columns or rename columns.
