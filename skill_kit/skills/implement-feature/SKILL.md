---
name: implement-feature
description: Executes additive work by introducing new behavior. Use when new functionality is being added to an existing codebase.
---

# Implement Feature

## When To Use

Use when new behavior is being introduced to the project.

Do not use when the task is read-only review or behavior-preserving restructuring — use `review-code` or `refactor-code` instead.

## Mandatory Behavior

### 1. Frame The Change

Before editing, state:
- user-facing intent of the change
- touched components or abstractions
- expected blast radius
- success criteria
- intended verification approach

If intent or scope is ambiguous, stop and surface the ambiguity before editing.

### 2. Read Required Context

Before editing, read:
- the relevant architecture and design documentation
- conventions or coding standards for the project
- existing implementations in the affected area to understand established patterns

### 3. Implement Under Project Boundaries

Follow project coding conventions.

If a needed abstraction is missing, stop and surface the gap instead of bypassing the project's established patterns.

### 4. Add Or Adjust Tests

Add or update tests proportional to the risk level of the change.

### 5. Verify

Run the verification checks appropriate to what changed: type checks, linting, unit tests, and integration tests as required.

If any required check fails, fix the underlying cause and re-run the full required set.

## Output Contract

Report:
- changed files
- verification commands run and their results
- any intentionally skipped checks with reasons
