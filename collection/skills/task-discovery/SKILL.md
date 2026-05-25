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

## Prerequisites

Before discovery, confirm:
- The user request describes a task, feature, bug, refactor, or implementation goal to investigate.
- The relevant repository context can be read.
- Discovery can proceed without modifying files.
- The expected output is context, constraints, risks, and open questions, not implementation.

If the task target is unclear, ask the smallest clarifying question before reading broadly.

## Safety Constraints

- Do not edit, create, delete, stage, or commit files during discovery.
- Do not infer contracts, ownership, or intended behavior from names alone; label unsupported conclusions as assumptions.
- Do not expand discovery into implementation planning beyond identifying context, constraints, risks, and open questions.

## Scope

Examine:
- Relevant files, components, and their dependencies
- Existing code patterns and established conventions
- Architecture, contracts, module boundaries, and potential risk areas

## Stop Conditions

- If the task scope or relevant entry points cannot be identified from the provided context, stop and ask the user to clarify the scope before reading further.
- Stop and report discovery as blocked when the task goal or likely entry points cannot be identified.
- Stop and report blocked when required files, dependencies, or project documentation cannot be read.
- Stop and ask for clarification when multiple plausible scopes exist and choosing one would materially change the findings.
- Stop when continuing would require making product, architecture, or implementation decisions instead of discovering context.

## Procedure

1. Identify the files and components directly relevant to the task.
2. Map dependencies and calling code that may be affected.
3. Note existing patterns and conventions in the affected area.
4. Identify contracts, invariants, architectural boundaries, and risk areas.
5. Report findings as context and constraints.

When several entry points could match the request, inspect the most directly named area first and state that chosen scope. If two or more scopes are equally plausible and would produce different discovery results, stop and ask for clarification.

## Verification

Before emitting discovery output, verify:
- Each context claim is supported by a source read or clearly marked as an assumption.
- Relevant dependencies, callers, tests, or docs were checked when they affect scope.
- Open questions contain only gaps that affect implementation scope, correctness, or risk.

## Output Contract

Emit:

`Skill: task-discovery - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed`, `partial`, or `blocked` |
| Task Scope | Task, feature, bug, refactor, or area investigated |
| Sources Read | Files, docs, tests, commands, or evidence inspected |
| Context | Relevant code segments, dependency information, and patterns observed |
| Constraints / Risks | Contracts, boundaries, invariants, risk areas, or `none` |
| Assumptions | Inferences used, or `none` |
| Open Questions / Blockers | Clarifications or unreadable context, or `none` |

Use `partial` or `blocked` when important context cannot be inspected.
