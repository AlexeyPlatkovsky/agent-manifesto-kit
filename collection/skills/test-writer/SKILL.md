---
name: test-writer
description: Writes tests before production code changes (TDD red phase). Use when establishing the test contract for a new feature or bug fix.
---

## Scope

- Implement the TDD red phase by writing failing tests that express the desired behavior before any production code is changed.

## Prerequisites

Before writing tests, confirm:
- The user requested or approved TDD red-phase test creation.
- The desired behavior, bug reproduction, or acceptance criteria are clear enough to express as tests.
- Production code for the behavior has not already been changed in this task.
- Relevant test framework, existing test patterns, commands, and code under test can be inspected.
- Tests can be added without overwriting unrelated user work.

If any item is false, stop and report what is missing.

## Safety Constraints

- Do not edit production code during test writing.
- Do not change existing passing tests, fixtures, snapshots, or expectations unless required to express the approved new behavior.
- Do not make tests fail through invalid setup, syntax errors, missing imports, timing assumptions, or intentionally broken assertions.
- Do not invent requirements, edge cases, permissions, defaults, or user-facing behavior not supported by user input or repository evidence.
- Do not overwrite unrelated user changes.

## Stop Conditions

- Stop and report test writing as blocked when the expected behavior cannot be stated as observable assertions.
- Stop and report blocked when required test context, fixtures, commands, or code under test cannot be read.
- Stop and report blocked when the test runner cannot execute because of configuration, dependency, environment, or credential issues.
- Stop and report blocked when production code has already been changed and the work is no longer a TDD red phase.
- Stop and report blocked when creating the tests would require changing production code, product decisions, schemas, external services, or unrelated tests.

## Procedure

1. Review available requirements, acceptance criteria, bug reproduction, or discovery notes.
2. Identify expected behaviors and edge cases to cover.
3. Create test cases that express the desired behavior.
4. Run tests to confirm they fail initially (red phase confirmed).
5. Investigate any passing new tests and classify them as already-covered behavior or incomplete red-phase evidence.
6. Document failing tests as the implementation contract.

When multiple test scopes or assertion styles are plausible, choose the one that matches existing project test patterns and the smallest observable behavior contract. If multiple scopes are equally plausible and would test different behavior, stop and ask for clarification.

## Verification

Before reporting completion, verify:
- Each new test maps to a stated requirement, acceptance criterion, or bug reproduction.
- The failure reason demonstrates missing behavior rather than broken test setup.
- Existing unrelated tests were not changed or invalidated without explanation.
- Any passing new test is explained as already-covered behavior or incomplete red-phase evidence.

## Output Contract

Emit:

`Skill: test-writer - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed`, `skipped`, or `blocked` |
| Scope | Feature, bug, behavior, or contract covered |
| Test Files | Created or modified test files, or `none` |
| Sources Read | Requirements, code, tests, docs, or commands inspected |
| Red Phase Contract | Failing test cases and the behavior each asserts |
| Red Phase Evidence | Test command run and failure reason |
| Assumptions | Inferences used, or `none` |
| Coverage Gaps | Known missing cases, or `none` |
| Blockers | Missing context, unavailable runner, or non-red-phase state, or `none` |

Use `completed` only when newly written tests fail for the intended unmet behavior, not setup or syntax errors.

Use `blocked` when approved test cases cannot be red-confirmed; list red-confirmed cases in `Red Phase Evidence` and blocked cases in `Coverage Gaps` and `Blockers`.
