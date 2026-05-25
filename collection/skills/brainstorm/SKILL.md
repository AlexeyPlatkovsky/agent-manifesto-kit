---
name: brainstorm
description: Resolves high-impact design or setup decisions one question at a time before execution begins.
---

# Brainstorm

## Purpose

Use this skill to resolve open decisions that materially affect routing, structure, validation, reusable documentation, or capability design.

## When To Use

- A setup or design choice has multiple valid paths.
- Clarification requires evaluating trade-offs.
- The user must choose before implementation can proceed safely.

## When Not To Use

- The question is purely factual with no meaningful choice between options.
- A decision summary has already been confirmed.
- Execution has already started and no new high-impact decision appeared.

## Prerequisites

Before asking a brainstorm question, confirm:
- There is an unresolved high-impact decision.
- The decision has two or three meaningful, comparable options.
- The answer will affect routing, structure, validation, reusable documentation, or capability design.
- No confirmed decision summary already covers the choice.

## Rules

1. Ask exactly one question per turn.
2. Provide two or three concrete, comparable options.
3. State the trade-off, risk, or constraint for each option.
4. Include a free-form correction path when listed options may be incomplete.
5. Stop and wait for the user's answer before asking the next question.
6. Do not edit files during brainstorming.
7. End with a decision summary and wait for user confirmation before execution begins.
8. If the user's answer is ambiguous or non-committal, state your interpretation explicitly ("I'll treat this as option X — correct me if wrong") and wait for confirmation before recording the decision.
9. If the choice is factual, low-impact, already decided, or lacks meaningful trade-offs, do not use brainstorming; answer directly or ask the smallest factual clarification instead.
10. Do not present options as equally valid when user requirements, framework constraints, risk, or feasibility make one option materially stronger.

## Verification

Before emitting the decision summary, verify that every recorded decision includes the selected option and any user-stated caveat, and that no unresolved high-impact decision remains in the brainstorming scope.

## Output Contract

When all decisions are made, emit:

`Skill: brainstorm - output below`

Include:

| Decision | Selected Option | Caveat |
| --- | --- | --- |

Execution may begin only after the user confirms the summary.
