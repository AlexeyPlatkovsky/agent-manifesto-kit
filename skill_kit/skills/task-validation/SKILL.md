---
name: task-validation
description: Validates that the solution meets requirements and has no regressions. Use during the validate_solution workflow step.
---

# Task Validation

## Purpose

Confirm that the completed implementation satisfies original requirements and does not introduce regressions.

## When To Use

Use as the validation step after implementation is complete and before task closure.

## Procedure

1. Verify the implementation matches the original requirements.
2. Run tests and confirm they pass.
3. Check for regressions in affected areas.
4. Report validation result as **pass** or **fail**, with any issues found.

## Output Contract

Emit:

`Skill: task-validation - output below`

Then include:

| Result | Details |
| --- | --- |
| pass / fail | Issues found, or "none" |
