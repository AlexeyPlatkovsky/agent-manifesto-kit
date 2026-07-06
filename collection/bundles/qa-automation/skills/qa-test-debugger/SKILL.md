---
name: qa-test-debugger
description: Reproduces, diagnoses, and minimally fixes failing or flaky automated tests while preserving evidence about whether the cause is product code, test code, environment, or unknown.
---

## Scope

- Investigate failing, flaky, or suspicious automated tests.
- Apply the smallest safe fix when the root cause is clear and within the approved task scope.

## Boundaries

- Do not delete or weaken assertions to make tests pass.
- Do not update snapshots, fixtures, or expectations unless evidence shows the expected behavior intentionally changed.
- Do not mask product defects by changing tests.
- Do not run broad suites before a targeted reproduction unless project conventions require it.

## Stop Conditions

Stop and report blocked when:

- the failing command, scenario, or artifact cannot be identified
- the failure cannot be reproduced and no useful artifacts exist
- required credentials, services, browsers, or dependencies are unavailable
- the likely fix requires a product decision outside the approved task

## Procedure

If any stop condition applies, halt the procedure and report the blocker under the output
contract.

Apply Boundaries throughout; if the requested fix requires violating one, stop and report
`blocked`.

1. Record the failing command, scenario, environment, and available artifacts.
2. Reproduce with the narrowest command or browser flow.
3. Inspect test code, product code, fixtures, configuration, and artifacts relevant to the failure.
4. Classify the likely cause as product defect, test defect, selector drift, fixture/data issue, environment blocker, flaky timing risk, or unknown.
5. Apply a minimal fix only when the cause is clear and in scope.
6. Re-run targeted verification and report any residual risk.

## Output Contract

Emit:

`Skill: qa-test-debugger - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed`, `skipped`, or `blocked` |
| Failure Scope | Test, command, scenario, or artifact investigated |
| Reproduction | Command or browser flow and observed result |
| Root Cause Classification | Product defect, test defect, selector drift, fixture/data issue, environment blocker, flaky timing risk, unknown |
| Changed Files | Files changed with one-line reason, or `none` |
| Verification | Commands run and pass/fail/skipped/blocked status |
| Evidence | Logs, screenshots, traces, reports, or code references |
| Residual Risk | Remaining uncertainty, or `none` |
| Blockers | Missing context, unavailable environment, or out-of-scope decision, or `none` |
