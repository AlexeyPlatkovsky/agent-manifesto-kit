# Recommended Companions

Optional capabilities from the general collection that complement the QA Automation bundle.
None are required: the bundle works as a self-contained test creation, debug, and review
workflow. These are surfaced as opt-in suggestions by adoption tooling, including
`agentkit adopt`.

See `../kit-adopt/conventions/recommended-companions.md` for the declaration format.

| Companion | Kind | Suggested source | Touchpoint |
| --- | --- | --- | --- |
| `playwright-cli` | skill | `collection/skills/playwright-cli/` | General browser automation beyond the QA-specific CLI workflow |
| `task-validation` | skill | `collection/skills/task-validation/` | Final validation reporting after test changes |
| `documentation-maintenance` | skill | `collection/skills/documentation-maintenance/` | Updating testing docs, commands, or workflow notes |
| `task-complete` | skill | `collection/skills/task-complete/` | Closing routed non-trivial QA work |
| `test-review` | skill | `collection/skills/test-review/` | Lightweight review when an isolated agent is not needed |
| `code-reviewer` | agent | `collection/agents/code-reviewer.md` | Independent review when QA changes also touch product code |
| `docs-manager` | agent | `collection/agents/docs-manager.md` | Broader documentation stewardship after QA workflow changes |
| `frontend-audit` | skill | `collection/skills/frontend-audit/` | Accessibility and responsive UI audit during browser-based QA |
