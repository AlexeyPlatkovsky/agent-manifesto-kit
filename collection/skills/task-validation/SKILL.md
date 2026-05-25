---
name: task-validation
description: Validates that the solution meets requirements and has no regressions. Use during the validate_solution workflow step.
---

# Task Validation

## Purpose

Confirm that the completed implementation satisfies original requirements and does not introduce regressions.

## When To Use

Use as the validation step after implementation is complete and before task closure.

## Prerequisites

Before validating, confirm:
- The original requirements, acceptance criteria, or requested outcome are available.
- The completed implementation, changed files, diff, or artifact set can be inspected.
- The expected validation checks are known from the routed plan, project conventions, package scripts, docs, or repository evidence.
- The environment can run at least one meaningful automated or manual validation check.

If required validation context is missing, report `blocked` and name the missing input.

## Safety Constraints

- Do not modify files, update snapshots, regenerate artifacts, or change test expectations during validation.
- Do not mark validation as passed from raw command output alone; summarize the gate, evidence, and result.
- Do not ignore failing checks because they appear unrelated unless the reason is stated.
- Do not invent acceptance criteria or validation coverage not supported by the request or repository evidence.

## Stop Conditions

- If tests cannot execute due to environment or configuration issues (missing runner, broken setup, missing dependencies), do not report `fail` — report `blocked` and describe the blocker.
- Stop and report `blocked` when original requirements or acceptance criteria cannot be identified.
- Stop and report `blocked` when the implementation or affected surface cannot be inspected.
- Stop and report `blocked` when required tests or checks cannot run because of missing dependencies, broken setup, unavailable services, or missing credentials.
- Stop and report `blocked` when no meaningful validation path is available for the changed behavior.
- Stop and report `blocked` when a planned validation gate was skipped without a reason.

## Procedure

1. Verify the implementation matches the original requirements.
2. Run tests and confirm they pass.
3. Check for regressions in affected areas.
4. Report validation result as **pass**, **fail**, or **blocked**, with any issues found.

Choose the smallest meaningful validation set that covers the changed behavior and likely regressions. If several validation paths are plausible and differ materially in confidence or cost, state the chosen path and why; if no path is clearly adequate, report blocked.

## Verification

Before emitting the validation result, verify:
- Every original requirement or acceptance criterion was checked, marked not applicable, or listed as blocked.
- Each changed or affected area has at least one relevant validation signal.
- Failures distinguish implementation defects from environment/setup blockers.
- Skipped checks include a concrete reason and residual risk.

## Output Contract

Emit:

`Skill: task-validation - output below`

Then include:

| Field | Content |
| --- | --- |
| Overall Result | `pass`, `fail`, or `blocked` |
| Scope | Requirement, feature, fix, refactor, or artifact set validated |
| Requirements Checked | Requirements or acceptance criteria checked, or `unknown` |
| Validation Gates | Each gate with status `pass`, `fail`, `skipped`, or `blocked` |
| Evidence | Commands, tests, inspections, or scenario checks performed |
| Issues Found | Failures or regressions, or `none` |
| Assumptions | Inferences used, or `none` |
| Blockers | Missing context, environment issue, or unavailable check, or `none` |

`Overall Result` may be `pass` only when all required validation gates passed or skipped gates are explicitly justified and non-blocking.
