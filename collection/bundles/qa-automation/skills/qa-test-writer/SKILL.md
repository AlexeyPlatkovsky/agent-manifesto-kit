---
name: qa-test-writer
description: Creates or updates automated tests from an approved specification, bug reproduction, acceptance criterion, or exploration handoff without changing product behavior.
---

## Scope

- Add or update automated tests for existing or requested behavior.
- Use when the test target and expected observable behavior are clear enough to assert.

## Boundaries

- Do not change production code.
- Do not invent requirements, edge cases, permissions, defaults, or user-facing behavior.
- Do not rewrite unrelated tests, snapshots, fixtures, or helpers.
- Do not use sleeps, arbitrary timeouts, brittle selectors, or broad assertions when deterministic alternatives exist.

## Stop Conditions

Stop and report blocked when:

- expected behavior cannot be expressed as observable assertions
- the relevant test framework, command, fixture, or code under test cannot be identified
- adding the test requires a product decision or production-code change
- the test runner cannot execute because of missing dependencies, credentials, or environment setup

## Procedure

If any stop condition applies, halt the procedure and report the blocker under the output
contract.

Apply Boundaries throughout; if the requested test requires violating one, stop and report
`blocked`.

1. Read the test specification, bug reproduction, acceptance criterion, or exploration handoff.
2. Inspect nearby tests, helpers, fixtures, and project test conventions.
3. Choose the smallest test scope that protects the behavior.
4. Write or update tests using existing patterns before introducing new helpers.
5. Run the narrowest meaningful test command when the environment supports it.
6. Report verification per the project's QA verification convention.

## Output Contract

Emit:

`Skill: qa-test-writer - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed`, `skipped`, or `blocked` |
| Scope | Behavior, scenario, or bug reproduction covered |
| Test Files | Created or modified test files, or `none` |
| Sources Read | Specs, tests, code, docs, fixtures, or commands inspected |
| Assertions Added | Behaviors asserted by the tests |
| Verification | Commands run and pass/fail/skipped/blocked status |
| Assumptions | Inferences used, or `none` |
| Coverage Gaps | Known missing cases, or `none` |
| Blockers | Missing context, unavailable runner, or environment issue, or `none` |
