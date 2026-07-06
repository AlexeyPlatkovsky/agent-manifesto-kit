# QA Automation Bundle

QA Automation kit: a cohesive, project-agnostic set of capabilities for creating,
debugging, and reviewing automated tests with strong evidence trails, browser inspection,
and validation discipline.

This bundle is product output. It is meant to be copied into a consumer project and
adapted with minimal effort. The bundle is independently copyable as a unit; each item
below is also copyable on its own, subject to the dependencies listed.

## Contents

| Item | Type | Path | Depends on |
| --- | --- | --- | --- |
| `qa-verification` | convention | `conventions/qa-verification.md` | - |
| `qa-playwright-cli` | skill | `skills/qa-playwright-cli/` | - |
| `qa-test-writer` | skill | `skills/qa-test-writer/` | `qa-verification` |
| `qa-test-debugger` | skill | `skills/qa-test-debugger/` | `qa-verification` |
| `qa-explorer` | agent | `agents/qa-explorer.md` | `qa-verification` |
| `qa-test-reviewer` | agent | `agents/qa-test-reviewer.md` | `qa-verification` |
| `qa-test-from-spec` | pipeline | `pipelines/qa-test-from-spec.md` | skills + agents + `qa-verification` |
| `qa-test-debug` | pipeline | `pipelines/qa-test-debug.md` | skills + agents + `qa-verification` |
| Recommended companions | manifest | `RECOMMENDS.md` | optional companions only |

## Workflow Shape

The bundle separates four concerns:

- exploration before implementation
- test creation or debugging
- independent test review
- verification evidence before handoff

The pipelines are routing artifacts. They sequence the bundle's skills and agents, but do
not implement step logic themselves.

## Recommended Companions

`RECOMMENDS.md` lists optional general collection capabilities that complement QA
automation work, especially documentation maintenance, final validation, closure, code
review, and frontend audit or polish. None are required for the bundle to be copied.

## How to Copy

- Whole bundle: copy `collection/bundles/qa-automation/` into your project's capability area.
- A single item: copy its file or folder plus anything in the "Depends on" column.
- For live browser exploration, install and verify Playwright CLI before using
  `qa-playwright-cli`.
