---
name: brainstorm
description: Resolves high-impact design or setup decisions one question at a time before execution begins.
---

## Scope

- Resolve open decisions that materially affect routing, structure, validation, reusable documentation, or capability design.
- Use when a setup or design choice has multiple valid paths, clarification requires evaluating trade-offs, or the user must choose before implementation can proceed safely.
- Out of scope: purely factual questions with no meaningful choice; decisions already confirmed by a prior summary; execution already underway with no new high-impact decision.

## Safety Constraints

- Do not edit files during brainstorming.
- Do not present options as equally valid when user requirements, framework constraints, risk, or feasibility make one option materially stronger.

## Procedure

1. Confirm no prior decision summary already covers the choice.
2. Ask exactly one question per turn, with two or three concrete, comparable options and the trade-off, risk, or constraint for each.
3. For setup or profile choices, include a free-form correction path when the listed options may be incomplete or inaccurate.
4. Stop and wait for the user's answer before asking the next question.
5. If the user's answer is ambiguous or non-committal, state your interpretation explicitly ("I'll treat this as option X — correct me if wrong") and wait for confirmation before recording the decision.
6. End with a decision summary and wait for user confirmation before execution begins.

## Verification

Before emitting the decision summary, verify that every recorded decision includes the selected option and any user-stated caveat, and that no unresolved high-impact decision remains in the brainstorming scope.

## Output Contract

When all decisions are made, emit:

`Skill: brainstorm - output below`

Include:

`Status: completed | blocked`

`Scope: <decisions covered>`

`Blockers: none | <blocker>`

| Decision | Selected Option | Caveat |
| --- | --- | --- |

Execution may begin only after the user confirms the summary.
