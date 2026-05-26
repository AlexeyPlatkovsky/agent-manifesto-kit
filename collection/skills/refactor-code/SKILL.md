---
name: refactor-code
description: Behavior-preserving restructuring of existing code. Use when reshaping code without changing user-facing behavior.
---

## Scope

- Reshape existing code without changing user-facing behavior.

## Prerequisites

Before editing, confirm:
- The user requested or approved behavior-preserving restructuring.
- The code area, preserved behavior, and intended improvement are clear enough to state.
- Relevant implementation, tests, public API, configuration, and conventions can be read.
- A meaningful before-and-after verification path is available.
- The change can be made without overwriting unrelated user work.

If any item is false, stop and report what is missing.

## Safety Constraints

- Do not bundle unrelated cleanup, feature work, formatting churn, dependency changes, or test rewrites into the refactor.
- Do not change public API, persisted data shape, permissions, defaults, or user-visible behavior; if required, stop and treat the task as non-refactor work.
- Do not adjust tests to hide a behavior change.
- Do not overwrite unrelated user changes.

## Stop Conditions

Stop and report the refactor as blocked when:
- Behavior preservation cannot be stated concretely.
- Required context or public API boundaries cannot be inspected.
- The baseline verification fails before editing.
- The refactor would require a behavior change, breaking public API change, schema migration, generated artifact rewrite, new dependency, broad architecture change, or test expectation change.
- Existing architecture or project conventions conflict with the requested refactor.
- Required verification cannot be run or cannot provide meaningful evidence.

## Procedure

### 1. Frame The Refactor

Before editing, state:
- what is being reshaped and why
- what behavior must be preserved
- the protective tests that confirm preservation
- the intended verification approach

If the refactor crosses into system-level or shared infrastructure, stop and surface the risk before editing.

### 2. Read Required Context

Read the existing implementation thoroughly before editing.

Also read relevant architecture documentation, coding conventions, and the public API of the touched abstraction.

### 3. Establish A Behavior Baseline

Before editing, run targeted tests covering the touched behavior, plus type checks and linting.

If the baseline fails, stop and surface the failure instead of refactoring against an unstable state.

### 4. Refactor Under Project Boundaries

Follow project coding conventions. Preserve the public API of the touched abstraction.

Do not change behavior incidentally during a refactor. Do not bundle unrelated cleanup into the same refactor.

When multiple refactor approaches are plausible and differ materially in blast radius, public contract, ownership, or long-term maintainability, stop and surface the options instead of choosing silently.

### 5. Verify Preservation

After editing, re-run the same targeted tests from the baseline. Run the full test suite when shared or framework-level behavior is touched.

If a previously passing targeted test now fails, or if a test expectation had to change, stop and surface the behavior change. Test code may be restructured only to preserve existing expectations.

## Verification

Before reporting completion, verify:
- The diff is limited to behavior-preserving restructuring and test-code restructuring that preserves existing expectations.
- Baseline and final verification cover the same preserved behavior.
- No public API, persisted data shape, default, permission, or user-facing output changed unintentionally.
- Any failed or skipped verification is reported with enough context for follow-up.

## Output Contract

Emit:

`Skill: refactor-code - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed` or `blocked` |
| Scope | Code area, abstraction, or behavior refactored |
| Preserved Behavior | Behavior that was required to remain unchanged |
| Changed Files | Files changed, or `none` |
| Assumptions | Inferences used, or `none` |
| Baseline Verification | Commands/checks run before editing and results |
| Final Verification | Commands/checks run after editing and results |
| Skipped Checks | Checks not run with reasons, or `none` |
| Blockers | Remaining blockers, or `none` |

`Status` may be `completed` only when the refactor is applied and the smallest meaningful available baseline and final checks provide preservation evidence. Report unavailable or inapplicable checks under `Skipped Checks`; use `blocked` when no meaningful preservation evidence is available.
