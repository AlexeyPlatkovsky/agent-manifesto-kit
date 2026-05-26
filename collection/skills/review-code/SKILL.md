---
name: review-code
description: Read-only review of code changes, branches, diffs, or artifacts. Use to evaluate changes without implementing fixes.
---

## Scope

- Evaluate code changes, branches, diffs, or artifacts without implementing fixes.

## Prerequisites

Before reviewing, confirm the requested review depth is clear, or a default bug-risk review is acceptable and stated.

If the target scope is unclear, ask the smallest clarifying question before reviewing.

## Safety Constraints

- Do not modify files, apply fixes, stage changes, commit, or run destructive commands.
- Do not invent issues just to produce findings.
- Distinguish confirmed defects from risks, questions, and missing evidence.
- Do not treat style preferences as findings unless they create correctness, maintainability, or operational risk.

## Stop Conditions

Stop and report the review as blocked when:
- The target scope cannot be located or read.
- A code-change review is requested but no diff, branch, patch, file list, or artifact set is available.
- Required context is unavailable and reviewing without it would make findings speculative.
- The review would require executing fixes, changing files, or making product decisions.

## Procedure

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
- simplicity and unnecessary complexity
- duplication that creates maintenance, correctness, or behavior-drift risk
- public API or contract changes
- concurrency and CI/runtime risks when relevant

Prioritize confirmed correctness, regression, data-loss, security, compatibility, and test-quality issues before maintainability concerns. Ignore formatting-only issues unless they affect behavior, maintainability, or future breakage risk.

### 4. Produce Findings

Lead with findings ordered by severity with file and line references where available.

Use these sections:

- **Blocking** — must be fixed before handoff
- **Non-blocking** — should be addressed; can follow up
- **Questions** — ambiguities requiring clarification

Empty sections are allowed.

## Verification

Before emitting the review, verify:
- Every finding names the affected file and line when available.
- Each finding explains the risk and likely fix direction.
- Questions are limited to ambiguities that affect correctness, acceptance, or review confidence.
- Residual verification gaps are explicitly listed.

## Output Contract

Do not modify repository files.

Emit:

`Skill: review-code - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed`, `skipped`, or `blocked` |
| Scope | Files, branch, diff, patch, or artifact set reviewed |
| Sources Read | Code, docs, tests, diffs, or verification evidence inspected |
| Assumptions | Inferences used, or `none` |
| Findings | Blocking, non-blocking, and questions with file/line references where available |
| Verification Gaps | Missing or insufficient checks, or `none` |
| Blockers | Remaining blockers, or `none` |

Use `blocked` when required scope or evidence cannot be inspected.
