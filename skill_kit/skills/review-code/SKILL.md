---
name: review-code
description: Read-only review of code changes, branches, diffs, or artifacts. Use to evaluate changes without implementing fixes.
---

# Review Code

## When To Use

Use when the goal is to evaluate changes without implementing fixes.

Do not use when the goal is to implement — use `implement-feature` or `refactor-code` instead.

## Mandatory Behavior

### 1. Frame The Review Scope

State which files, branch, diff, or artifact set is in scope and what review depth is requested.

### 2. Load Relevant References

Read the architecture documentation, coding conventions, and verification requirements for the project before reviewing.

### 3. Inspect The Scope

For code changes, inspect in dependency order: from foundational components to consuming components.

Check:
- naming, placement, and layer conventions
- correctness and behavior preservation
- test coverage and quality
- verification sufficiency
- hidden coupling or boundary violations

### 4. Produce Findings

Lead with findings ordered by severity with file and line references where available.

Use these sections:

- **Blocking** — must be fixed before handoff
- **Non-blocking** — should be addressed; can follow up
- **Questions** — ambiguities requiring clarification

Empty sections are allowed.

## Output Contract

Do not modify repository files.

Emit:

`Skill: review-code - output below`

Then include the findings table. Note any residual verification gaps at the end.
