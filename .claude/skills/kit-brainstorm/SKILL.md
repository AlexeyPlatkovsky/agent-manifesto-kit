---
name: kit-brainstorm
description: Resolves high-impact design or setup decisions one question at a time when multiple valid paths exist and user choice is required before safe execution.
---

# Brainstorm

## Purpose

Use this skill to resolve open decisions that materially affect routing, structure, validation, reusable documentation, or capability design.

## Template Reference

This skill follows `.claude/docs/skill-template.md`.

## Scope

- Handle setup or design choices with multiple valid paths.
- Handle clarification that requires evaluating trade-offs.
- Stop when the question is purely factual, the decision summary is already confirmed, or execution has already started and no new high-impact decision appeared.

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

`Skill: kit-brainstorm - output below`

Include:

| Decision | Selected Option | Caveat |
| --- | --- | --- |

Execution may begin only after the user confirms the summary.
