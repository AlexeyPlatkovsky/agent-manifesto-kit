---
name: python-refactoring-code
description: Refactors existing Python code to improve clarity or reduce duplication without changing behavior. Use when the user asks to refactor, simplify, extract, rename, or restructure Python code.
---

# Refactoring Python Code

## When to use

The user asks to restructure existing Python code while preserving behavior. Not for new functionality or bug fixes.

## Preconditions

- Tests exist for the affected code paths. If not, STOP and request explicit user consent to either add tests first or proceed with a recorded risk acknowledgement.
- Lint and type checks pass before starting.

## Procedure

1. State the goal in one sentence (e.g., "extract `_normalize_email` to remove three duplicates").
2. Pick one named refactoring per change:
   - Extract function / class / module
   - Inline function / variable
   - Rename
   - Replace conditional with polymorphism or dispatch dict
   - Introduce dataclass / Pydantic model
   - Replace magic value with module constant
   - Move function / attribute between modules
3. Run tests, lint, and type-check after each step. If anything fails, revert.
4. Keep imports and public re-exports stable. Update `__all__` when present.
5. Do not change formatting, logging, or exception types as a side effect.

## What not to do

- No speculative abstractions or "while I'm here" cleanups.
- No new dependencies during refactor.
- No silent behavior changes (return types, exception types, log levels).
- Do not switch sync to async or vice versa.

## Output contract

Report:
- Named refactoring(s) applied
- Files touched with one-line summary each
- Test / lint / type-check command results (all green)
- Any observable change worth noting (e.g., file moved, import path changed)

## Stopping conditions

Stop and surface if:
- The change requires a public API change
- Tests do not cover the affected area
- Scope grows beyond one named refactoring
