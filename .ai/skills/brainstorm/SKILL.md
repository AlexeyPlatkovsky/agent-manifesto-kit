---
name: brainstorm
description: Resolves high-impact design or setup decisions one question at a time before execution.
---

# Brainstorm

## Purpose

Use this skill to resolve open decisions that materially affect routing, structure, validation, reusable documentation, or capability design.

## When To Use

- A setup or design choice has multiple valid paths.
- Clarification requires evaluating trade-offs.
- The user must choose before implementation can proceed safely.

## When Not To Use

- The question is purely factual.
- A decision summary has already been confirmed.
- Execution has already started and no new high-impact decision appeared.

## Rules

1. Ask exactly one question per turn.
2. Provide two or three concrete options.
3. State the trade-off, risk, or constraint for each option.
4. Include a free-form correction path when options may be incomplete.
5. Stop and wait for the user's answer.
6. Do not edit files during brainstorming.
7. End with a decision summary and wait for confirmation before execution.

## Output Contract

When all decisions are made, emit:

`Skill: brainstorm - output below`

Include:

| Decision | Selected Option | Caveat |
| --- | --- | --- |

Execution may begin only after the user confirms the summary.
