---
name: doc-writing-task-spec
description: Writes a clear task or user-story specification with goal, scope, acceptance criteria, and out-of-scope items. Use when the user asks for a task spec, ticket description, user story, or scoped work item ready for implementation.
---

# Writing a Task Specification

## When to use

The user wants a self-contained, implementable task spec — for a tracker ticket, internal doc, or AI agent handoff. Not for ADRs (`doc-writing-architecture-decision`) or full feature docs.

## Inputs required

- Problem statement or feature request
- Target audience (engineer, AI agent, designer)
- Known constraints (deadline, system, owners)

If the problem is exploratory ("we should look into X"), stop and ask for a single concrete outcome first.

## Spec template

```
# <Imperative title — what will be done>

## Goal
<One sentence: the user-visible or system-visible outcome.>

## Why
<2–4 sentences: the reason this is worth doing now. Cite the source: bug,
feedback, metric, dependency.>

## Scope
- In scope:
  - <bullet>
  - <bullet>
- Out of scope:
  - <bullet — list things a reader might assume are included>

## Acceptance criteria
1. Given <precondition>, when <action>, then <observable result>.
2. …

## Inputs / dependencies
- <APIs, designs, data, accounts, approvals>

## Risks and unknowns
- <bullet, with mitigation or "needs investigation">

## Notes
- <links to designs, related tickets, prior art>
```

## Procedure

1. State the goal in one sentence. If it does not fit one sentence, the task is too large — propose splitting.
2. Write 3–7 acceptance criteria in Given/When/Then form. Each must be independently testable.
3. Fill "Out of scope" with at least one item — defines the boundary.
4. List every dependency needed before work can start. If anything is missing, mark the spec as "blocked".
5. Identify risks honestly; do not omit ones that could derail the work.

## Quality checks

- Title is imperative and specific.
- Acceptance criteria are testable, not aspirational ("the system is faster" is not acceptable).
- No implementation prescription unless intentional ("use library X" only if it is a real constraint).
- Reader can start work without asking follow-up questions.

## Output contract

- The spec content
- A readiness verdict: Ready / Needs info / Blocked, with reasons

## Stopping conditions

Stop if:
- The goal cannot be reduced to a single sentence
- Acceptance criteria cannot be made testable
- The work depends on an unmade decision
