---
name: validation-report
description: Summarizes verification performed for non-trivial routed work so downstream gates can audit the result.
---

# Validation Report

## Purpose

Convert verification evidence into a visible validation artifact for non-trivial routed work.

## When To Use

Use after implementation or artifact edits when a downstream review, documentation, or completion gate needs to know what was verified.

## When Not To Use

- Trivial direct work.
- Raw command output with no routed handoff.
- Review-only tasks where no validation gate was planned.

## Inputs

- Planned validation gates from `kit-manager`.
- Commands, static checks, manual inspections, or scenario checks actually performed.
- Relevant outputs or failure summaries.

## Procedure

1. Compare planned validation gates with actual verification.
2. Mark each gate as passed, failed, skipped, or blocked.
3. Summarize evidence without pasting excessive raw output.
4. Name any residual risk or unverified area.

## Output Contract

Emit:

`Skill: validation-report - output below`

Include:

| Gate | Evidence | Status | Notes |
| --- | --- | --- | --- |

Status must be `passed`, `failed`, `skipped`, or `blocked`.
