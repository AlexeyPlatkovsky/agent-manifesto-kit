---
name: test-review
description: Reviews and strengthens tests during the TDD green or refactor phase. Use after initial tests pass to ensure comprehensive coverage before handoff.
---

# Test Review

## Purpose

Review tests after the initial implementation passes. Identify coverage, maintainability, flakiness, and convention issues before the task is closed.

## When To Use

Use after baseline tests pass or validation evidence is available to evaluate test quality.

## When Not To Use

- Before a baseline test contract or validation result exists.
- For production code changes — this skill reviews tests, not implementations.

## Prerequisites

Before reviewing tests, confirm:
- The test files, diff, branch, or artifact set in scope can be identified and read.
- The code under test can be inspected.
- Initial test validation has passed, or the current validation result is available.
- Relevant project test conventions, commands, and expected behavior can be inspected.

If the scope is unclear, ask the smallest clarifying question before reviewing.

## Safety Constraints

- Do not edit, create, delete, stage, or commit files.
- Do not add, remove, or refactor tests during test review.
- Do not change production code or test expectations.
- Do not invent coverage claims that are not supported by inspected tests, code, or validation output.

## Responsibilities

1. Confirm all tests written by `test-writer` now pass (green phase is confirmed).
2. Identify edge cases and regression scenarios not covered during initial test creation.
3. Recommend missing test cases for edge scenarios, error paths, and boundary conditions.
4. Identify readability and maintainability improvements while preserving existing behavior.
5. Evaluate overall test coverage and identify any remaining gaps.

Stop and report the test review as blocked when:
- The tests in scope cannot be located or read.
- The code under test cannot be inspected.
- The initial test result is unavailable and reviewing would make findings speculative.
- A requested action would require editing tests, changing implementation, or making product decisions.

Evaluate tests on:
- correctness: the test verifies the behavior it claims to protect
- maintainability: setup, naming, assertions, and fixtures are clear and localized
- flakiness risk: timing, ordering, external services, randomness, filesystem, network, or environment coupling
- convention alignment: file placement, naming, structure, and project test patterns

This skill reviews tests as artifacts. Use a broader code-review capability when implementation quality, production behavior, or cross-cutting design risk is the primary concern.

## Verification

Before emitting the review, verify:
- Each finding is tied to a specific test, assertion, setup pattern, or missing behavior.
- Findings distinguish confirmed defects from risks and open questions.
- Recommended additions describe the scenario and expected assertion, not implementation steps.
- Remaining coverage gaps are explicit and not presented as completed work.

## Output Contract

Emit:

`Skill: test-review - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed`, `partial`, or `blocked` |
| Scope | Test files, diff, branch, or artifact set reviewed |
| Sources Read | Tests, code under test, docs, conventions, or validation evidence inspected |
| Initial Test Status | Passing, failing, unavailable, or not applicable |
| Findings | Prioritized findings for correctness, maintainability, flakiness, and convention alignment |
| Recommended Additions | Missing edge cases, regression scenarios, or assertions, or `none` |
| Assumptions | Inferences used, or `none` |
| Blockers | Missing scope, unreadable context, unavailable validation, or `none` |
