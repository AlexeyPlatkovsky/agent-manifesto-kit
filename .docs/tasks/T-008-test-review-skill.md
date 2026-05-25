# T-008 — `test-review` skill

**Epic:** 2 — Skills
**Feature:** 2.3 — `test-review` skill
**Status:** todo
**Dependencies:** T-002

## Goal

Author the `test-review` skill: reviews tests for correctness, maintainability, flakiness, and alignment with project conventions.

## Deliverables

- `.collection/skills/test-review/SKILL.md`

## Behavior outline

When triggered (typically after tests are added or modified), the skill should guide the assistant to:

1. Read the test files in scope and the code under test.
2. Evaluate each test on: correctness (does it actually verify the claim), maintainability (clarity, dependencies, setup cost), flakiness risk (timing, environment, ordering), convention alignment (file location, naming, structure).
3. Surface a prioritized list of findings with concrete suggestions.
4. Stop without modifying tests — output is a review, not a refactor.

## Acceptance criteria

- Conforms to [skill-format.md](T-002-skill-format-convention.md).
- Atomic: produces a written review; does not modify tests; does not call other skills or agents.
- `triggers` field is specific (after test changes, on explicit review request).
- Distinguishes itself from a generic code review by focusing on the four review dimensions above.
- Includes a concrete usage example.

## Notes

- Differentiate clearly from the `code-reviewer` agent ([T-010]): this skill reviews **tests as artifacts**, the agent reviews **implementation quality**. Cross-reference in the body where useful.

[T-010]: T-010-code-reviewer-agent.md
