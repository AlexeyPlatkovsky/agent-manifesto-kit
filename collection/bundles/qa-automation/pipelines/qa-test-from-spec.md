# Pipeline: QA Test From Spec

## Purpose

Pre-defined routing plan for creating automated tests from a specification, bug
reproduction, acceptance criterion, user story, or exploration request.

This pipeline is a routing artifact. It sequences existing capabilities. It does not
implement step logic and does not emit its own output artifact.

## When to Apply

- The user asks to create automated tests from a described behavior.
- The user asks to add regression coverage for a bug reproduction.
- The user asks to cover a UI, API, component, or workflow scenario with tests.

Do not use this pipeline for pure product implementation without test creation, broad test
suite audits, or one-line obvious test edits classified as trivial by the local manager.

## Inputs

- Specification, acceptance criterion, bug reproduction, or target scenario.
- Target test type when known: UI, API, integration, component, unit, visual, accessibility, or other.
- Known commands, docs, fixtures, app URLs, or artifacts when available.

## Stages

If any Stop Condition applies, halt the pipeline and report the blocker instead of advancing.

| Stage | Capability | Required Visible Artifact |
| --- | --- | --- |
| 1. Intake | direct - confirm scope, target behavior, and available commands | concise scope note |
| 2. Explore | `Agent: qa-explorer` | `Agent: qa-explorer - output below` |
| 3. Write tests | `Skill: qa-test-writer` | `Skill: qa-test-writer - output below` |
| 4. Review tests | `Agent: qa-test-reviewer` | `Agent: qa-test-reviewer - output below` |
| 5. Verify | direct - run gates defined by `qa-verification` and project commands | validation evidence |
| 6. Documentation impact | direct - update or report docs impact if test commands, workflows, or behavior changed | docs impact note |
| 7. Closure | direct - summarize changed files, validation, residual risk, and next steps | closure summary |

Do not advance past a stage whose expected visible artifact is missing.

## Revision Rules

- `Approve`: continue to verification.
- `Approve with minor fixes`: apply the cited fixes, re-run targeted verification, and continue.
- `Needs revision`: return to the writing stage with the findings. Repeat at most two cycles.
- `Reject`: return to exploration because the test approach does not match the evidence or scope.

## Authority Sources

- the `qa-verification` convention
- project test conventions, docs, package scripts, CI config, and nearby tests
- the user's approved specification or bug reproduction

## Stop Conditions

- The expected behavior cannot be stated as observable assertions.
- Required test commands, frameworks, fixtures, or credentials are unavailable.
- The reviewer still reports blocking findings after two revision cycles.
- Verification is blocked and no meaningful alternate validation path exists.

## Output Contract

The pipeline emits no artifact of its own. Each stage emits its own contract artifact as
listed above.
