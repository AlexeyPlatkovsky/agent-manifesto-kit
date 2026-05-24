---
name: test-writer
description: Writes tests before production code changes (TDD red phase). Use when establishing the test contract for a new feature or bug fix.
---

# Test Writer

## Purpose

Implement the TDD red phase by writing failing tests that express the desired behavior before any production code is changed.

## When To Use

Use before any production code changes when following a test-driven development workflow.

## When Not To Use

- After production code has already been changed — tests written after the fact are not the TDD red phase.
- For refactoring tasks where the goal is behavior preservation, not behavior definition.

## Procedure

1. Review the discovery plan and requirements.
2. Identify expected behaviors and edge cases to cover.
3. Create test cases that express the desired behavior.
4. Run tests to confirm they fail initially (red phase confirmed).
5. Validate that any passing tests indicate incomplete test coverage, not complete implementation.
6. Document failing tests as the implementation contract.

## Output Contract

Emit:

`Skill: test-writer - output below`

Then include:

| Field | Content |
| --- | --- |
| Test files | Created or modified files |
| Red phase contract | Failing test cases written |
| Confirmation | All written tests fail before production code changes |
| Coverage gaps | Any identified gaps |
