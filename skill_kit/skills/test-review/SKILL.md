---
name: test-review
description: Reviews and strengthens tests during the TDD green or refactor phase. Use after initial tests pass to ensure comprehensive coverage before handoff.
---

# Test Review

## Purpose

Review and strengthen tests after the initial implementation passes. Ensure coverage is complete and tests are maintainable before the task is closed.

## When To Use

Use after `test-writer` tests pass (the TDD green phase) to validate and improve coverage quality.

## When Not To Use

- Before the initial tests pass — run `test-writer` first.
- For production code changes — this skill reviews tests, not implementations.

## Responsibilities

1. Confirm all tests written by `test-writer` now pass (green phase is confirmed).
2. Identify edge cases and regression scenarios not covered during initial test creation.
3. Add missing test cases for edge scenarios, error paths, and boundary conditions.
4. Improve test readability and maintainability while preserving existing behavior.
5. Evaluate overall test coverage and identify any remaining gaps.

## Output Contract

Report:
- confirmation that all initial tests pass
- additional test cases added, if any
- coverage gaps identified with recommended additions
- any tests removed or refactored with reasons
