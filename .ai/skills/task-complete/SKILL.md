---
name: task-complete
description: Produces the required closure table for non-trivial routed work.
---

# Task Complete

## Purpose

Close non-trivial routed work by reporting what actually happened and confirming required visible artifacts exist.

## When To Use

Use as the final step for non-trivial routed work after validation, review, and documentation maintenance gates are complete or explicitly skipped.

## When Not To Use

- Trivial direct work.
- Work that did not go through routed execution.
- When a required planned output artifact is missing.

## Procedure

1. Review the manager plan.
2. Confirm every planned routed handoff has its expected visible output artifact.
3. Include every executed, skipped, blocked, or changed planned step.
4. If a required artifact is missing, report closure as blocked and name the missing artifact.

## Output Contract

Emit:

`Skill: task-complete - output below`

Then provide exactly this three-column table:

| Step | Skill / Agent | Comment |
|------|---------------|---------|

Do not add columns or rename columns.
