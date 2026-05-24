# T-010 — `code-reviewer` agent

**Epic:** 3 — Agents
**Feature:** 3.1 — `code-reviewer` agent
**Status:** todo
**Dependencies:** T-003

## Goal

Author the `code-reviewer` agent: performs focused review of implementation quality, risks, and missed requirements. The kit's reference example of when an agent (not a skill) is justified.

## Deliverables

- `.claude/agents/code-reviewer/AGENT.md`

## Behavior outline

When invoked, the agent should:

1. Read changed code in isolated context (the whole point of being an agent — main thread context stays clean).
2. Evaluate: correctness, risks (security, concurrency, data loss), missed requirements vs. the original task, maintainability, fit with surrounding patterns.
3. Output a structured review: high-priority findings, lower-priority findings, questions, explicit "looks good" calls where they apply.
4. Stop after producing the review. No code edits.

## Acceptance criteria

- Conforms to [agent-format.md](T-003-agent-format-convention.md): required frontmatter including `when_to_use` and `when_not_to_use`.
- `when_not_to_use` explicitly excludes: trivial changes (no review value), test-only changes (use `test-review` skill instead), purely cosmetic edits.
- The body justifies why this is an agent rather than a skill: context isolation, judgment-heavy review, length of input.
- Cross-references the `test-review` skill ([T-008]) so consumers don't confuse them.
- Includes a concrete usage example.

## Notes

- This agent and `test-review` skill have distinct scopes; the convention rule "no duplicate roles" is satisfied because tests-as-artifacts vs. code-quality review are different evaluations.

[T-008]: T-008-test-review-skill.md
