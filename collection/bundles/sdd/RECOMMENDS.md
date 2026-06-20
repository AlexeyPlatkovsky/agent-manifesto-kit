# Recommended Companions

Optional capabilities from the general collection that complement the SDD bundle across the
spec-to-build-to-verify loop. None are required: the SDD bundle works fully on its own. These
are surfaced as opt-in suggestions by `kit-adopt` and by the SDD pipelines. If a companion is
absent or renamed in the kit, skip it.

See `../kit-adopt/conventions/recommended-companions.md` for the declaration format.

| Companion | Kind | Suggested source | Touchpoint |
| --- | --- | --- | --- |
| `brainstorm` | skill | `collection/skills/brainstorm/` | Shaping `idea.md` and scope before authoring |
| `business-analyst` | skill | `collection/skills/business-analyst/` | Clarifying `features/*/requirements.md` and acceptance criteria |
| `task-discovery` | skill | `collection/skills/task-discovery/` | Breaking work into `tasks.md` |
| `task-validation` | skill | `collection/skills/task-validation/` | Validating `tasks.md` before implementation |
| `implement-feature` | skill | `collection/skills/implement-feature/` | Executing a feature's tasks (the build step) |
| `test-writer` | skill | `collection/skills/test-writer/` | Turning `scenarios.md` into automated tests |
| `test-review` | skill | `collection/skills/test-review/` | Reviewing tests against the scenarios |
| `code-reviewer` | agent | `collection/agents/code-reviewer.md` | Reviewing implementation against the spec |
| `documentation-maintenance` | skill | `collection/skills/documentation-maintenance/` | Keeping docs in sync after the build |
| `prepare-release-notes` | skill | `collection/skills/prepare-release-notes/` | Closing a `roadmap.md` milestone |
