---
name: implement-feature
description: Executes additive work by introducing new behavior. Use when new functionality is being added to an existing codebase.
---

# Implement Feature

## When To Use

Use when new behavior is being introduced to the project.

Do not use when the task is read-only review or behavior-preserving restructuring — use `review-code` or `refactor-code` instead.

## Prerequisites

Before editing, confirm:
- The user requested or approved adding new behavior.
- The desired behavior, affected workflow, and success criteria are clear enough to implement.
- Relevant code, tests, configuration, conventions, and project documentation can be read.
- The change can be made without overwriting unrelated user work.

If any item is false, stop and report what is missing.

## Safety Constraints

- Do not bundle unrelated cleanup, refactors, formatting churn, or dependency upgrades into the feature.
- Do not bypass established abstractions, layer boundaries, or project conventions to make the feature fit.
- Do not invent product rules, defaults, permissions, or user-facing behavior not supported by the request or repository evidence.
- Do not overwrite unrelated user changes.

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

When multiple implementation approaches are plausible and differ materially in blast radius, public contract, persistence model, or long-term ownership, stop and surface the options instead of choosing silently.

Stop and report the implementation as blocked when:
- The requested behavior or success criteria cannot be stated concretely.
- Required implementation context cannot be read.
- The change requires a breaking public API change, schema migration, destructive data operation, new dependency, security/auth change, generated artifact rewrite, or broad architectural change not explicitly approved.
- Existing architecture or project conventions conflict with the requested approach.
- Required verification cannot be run or cannot provide meaningful evidence.

### 4. Add Or Adjust Tests

Add or update tests proportional to the risk level of the change.

### 5. Verify

Run the verification checks appropriate to what changed: type checks, linting, unit tests, and integration tests as required.

If any required check fails, fix the underlying cause and re-run the full required set.

Before reporting completion, verify:
- The diff is limited to the requested feature and necessary supporting changes.
- Tests or checks cover the new behavior at the appropriate risk level.
- Any failed or skipped verification is reported with enough context for follow-up.

## Output Contract

Emit:

`Skill: implement-feature - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed` or `blocked` |
| Scope | Feature, behavior, or workflow implemented |
| Changed Files | Files changed, or `none` |
| Assumptions | Inferences used, or `none` |
| Verification | Commands/checks run and results |
| Skipped Checks | Checks not run with reasons, or `none` |
| Blockers | Remaining blockers, or `none` |

`Status` may be `completed` only when the requested behavior is implemented and required verification has passed or skipped checks are justified.
