# QA Verification

## Purpose

Define the shared evidence standard for QA automation work: test creation, test debugging,
browser exploration, and review handoffs.

## Standards

Prefer the smallest validation set that exercises the changed or failing behavior. Use the
project's own scripts, test runner, docs, and CI configuration as the source of truth for
commands.

Every QA handoff should record:

- the test target or failing scenario
- the command, browser flow, or inspection used as evidence
- whether each gate passed, failed, was skipped, or was blocked
- why any skipped or blocked gate was not run
- artifact paths for screenshots, traces, videos, snapshots, or logs used as evidence

Classify findings with these labels:

- `CONFIRMED_FROM_CODE` for evidence tied to files, diffs, tests, configs, or docs
- `CONFIRMED_FROM_LIVE_UI` for evidence observed through browser automation
- `CONFIRMED_FROM_ARTIFACT` for traces, videos, screenshots, logs, or test reports
- `UNKNOWN` when required evidence is unavailable

Do not treat live UI evidence as a substitute for test-run evidence when the task changes
automated tests. Do not treat passing tests as proof of visual, accessibility, or browser
state claims unless those claims are directly asserted or supported by artifacts.

## Failure Classification

When a test or browser check fails, classify the likely source:

- product defect
- test defect
- selector or locator drift
- fixture or data setup problem
- environment, dependency, or credential blocker
- flaky timing or synchronization risk
- unknown

Use `unknown` only after checking the relevant code, test output, and available artifacts.

## Reporting

A QA validation report should be concise and auditable. Include exact commands and artifact
paths, but summarize long logs instead of pasting them wholesale.
