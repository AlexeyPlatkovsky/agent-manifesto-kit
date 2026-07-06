# Pipeline: QA Test Debug

## Purpose

Pre-defined routing plan for reproducing, diagnosing, fixing, and validating failing or
flaky automated tests.

This pipeline is a routing artifact. It sequences existing capabilities. It does not
implement step logic and does not emit its own output artifact.

## When to Apply

- The user asks to fix a failing automated test.
- The user asks to investigate a flaky, hanging, or suspicious test.
- CI or local validation reports a test failure that needs root-cause analysis.

Do not use this pipeline for creating new coverage from a clean specification; use
`qa-test-from-spec` for that workflow.

## Inputs

- Failing command, CI check, test name, trace, screenshot, video, report, or log.
- Relevant branch, diff, changed files, or recent behavior change when known.
- Environment constraints such as browser, service, credential, or fixture availability.

## Stages

If any Stop Condition applies, halt the pipeline and report the blocker; Revision Rules only
govern completed stage outputs.

| Stage | Capability | Required Visible Artifact |
| --- | --- | --- |
| 1. Intake | direct - capture failing command, artifacts, and expected behavior source | concise failure scope note |
| 2. Explore failure | `Agent: qa-explorer` | `Agent: qa-explorer - output below` |
| 3. Diagnose and fix | `Skill: qa-test-debugger` | `Skill: qa-test-debugger - output below` |
| 4. Review tests | `Agent: qa-test-reviewer` when tests changed; direct skip note when no tests changed | reviewer artifact or skip note |
| 5. Verify | direct - run gates defined by `qa-verification` and project commands | validation evidence |
| 6. Documentation impact | direct - update or report docs impact if commands, workflows, or known failure modes changed | docs impact note |
| 7. Closure | direct - summarize root cause, changes, validation, residual risk, and next steps | closure summary |

Do not advance past a stage whose expected visible artifact is missing.

## Revision Rules

- If reproduction is blocked, stop and report the blocker with available evidence.
- If root cause is `unknown`, stop after diagnosis unless the user approves an exploratory fix.
- If review reports blocking findings, return to diagnosis and fix. Repeat at most two cycles.
- If verification fails for the same reason after two fix cycles, stop and surface the remaining failure.

## Authority Sources

- the `qa-verification` convention
- project test conventions, docs, package scripts, CI config, and nearby tests
- failure artifacts and the expected behavior source

## Stop Conditions

- The failing test, command, or artifact cannot be identified.
- Required dependencies, services, browsers, or credentials are unavailable.
- The likely fix requires a product decision outside the approved task.
- Verification is blocked and no meaningful alternate validation path exists.

## Output Contract

The pipeline emits no artifact of its own. Each stage emits its own contract artifact as
listed above.
