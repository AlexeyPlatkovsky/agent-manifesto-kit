---
name: refactor-code
description: Behavior-preserving restructuring of existing code. Use when reshaping code without changing user-facing behavior.
---

# Refactor Code

## When To Use

Use when the goal is to reshape existing code without changing user-facing behavior.

Do not use when behavior is being added, removed, or intentionally changed — use `implement-feature` instead.

## Mandatory Behavior

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

Follow project coding conventions. Preserve the public API of the touched abstraction unless the user has approved a breaking change.

Do not change behavior incidentally during a refactor.

Do not bundle unrelated cleanup into the same refactor.

### 5. Verify Preservation

After editing, re-run the same targeted tests from the baseline. Run the full test suite when shared or framework-level behavior is touched.

If a previously passing targeted test now fails or had to be modified, stop and surface the behavior change.

## Output Contract

Report:
- changed files
- before-and-after verification commands and results
- any intentionally skipped checks with reasons
