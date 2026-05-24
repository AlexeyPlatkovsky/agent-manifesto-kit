---
name: task-discovery
description: Gathers task context and identifies constraints before implementation begins. Use during discovery workflow steps to systematically understand the scope before acting.
---

# Task Discovery

## Purpose

Systematically gather task context and identify constraints before implementation begins. Prevent scope surprises and ensure the implementation plan is grounded in actual code state.

## When To Use

Use before non-trivial implementation work to establish a clear understanding of the existing landscape.

## When Not To Use

- For trivial, single-file changes where the scope is obvious.
- After implementation has already started — this is a pre-implementation skill.

## Scope

Examine:
- Relevant files, components, and their dependencies
- Existing code patterns and established conventions
- Architecture, contracts, module boundaries, and potential risk areas

## Procedure

1. Identify the files and components directly relevant to the task.
2. Map dependencies and calling code that may be affected.
3. Note existing patterns and conventions in the affected area.
4. Identify contracts, invariants, architectural boundaries, and risk areas.
5. Report findings as context and constraints.

## Output Contract

Emit:

`Skill: task-discovery - output below`

Then include:

| Category | Contents |
| --- | --- |
| Context | Relevant code segments, dependency information, and patterns observed |
| Constraints | Contracts, architectural boundaries, and identified risks |
