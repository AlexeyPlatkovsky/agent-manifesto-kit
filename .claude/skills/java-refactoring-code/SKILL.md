---
name: java-refactoring-code
description: Refactors existing Java code to improve clarity, reduce duplication, or apply a specific pattern without changing observable behavior. Use when the user asks to refactor, simplify, extract, rename, or restructure Java code.
---

# Refactoring Java Code

## When to use

The user asks to change the structure of existing Java code while preserving behavior. Not for adding new features (use `java-implementing-feature`) or fixing bugs.

## Preconditions

Refactoring without tests is unsafe. Before changing code:
- Confirm tests exist covering the affected methods. If none, ask the user whether to add tests first or to proceed with manual verification only.
- Confirm the build is green on the current branch.

## Procedure

1. State the refactoring goal in one sentence (e.g., "extract duplicated validation into `OrderValidator`").
2. Identify the smallest safe scope. Prefer one refactoring per change set.
3. Apply one of these named refactorings only:
   - Extract Method / Class / Interface
   - Inline Method / Variable
   - Rename
   - Replace conditional with polymorphism
   - Introduce parameter object
   - Replace magic number with constant
   - Move method/field
4. Run the full test suite after each refactoring step. If tests fail, revert and reassess.
5. Keep the public API unchanged unless the user approved a breaking change.
6. Do not mix refactoring with formatting-only or behavior-changing edits in the same commit.

## What not to do

- Do not "improve" code outside the requested scope.
- Do not introduce new abstractions speculatively (no future-proofing).
- Do not add or remove dependencies as part of a refactor.
- Do not change logging messages, exception types, or thread-safety guarantees.

## Output contract

Report:
- The named refactoring(s) applied
- Files touched with a one-line summary per file
- Test command and result (must be green)
- Any behavior-preserving but observable change (e.g., log line moved) — list explicitly

## Stopping conditions

Stop and surface to user if:
- The refactoring would require an API change
- Tests are missing for the affected area
- The scope grows beyond a single named refactoring
