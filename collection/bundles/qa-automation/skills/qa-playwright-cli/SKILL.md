---
name: qa-playwright-cli
description: Uses Playwright CLI for QA-focused live browser exploration, locator evidence, screenshots, traces, console output, and network evidence when repository evidence is insufficient.
---

## Scope

- Inspect live browser state for QA work when files, tests, page objects, fixtures, and docs do not reliably answer the question.
- Gather evidence for test creation, test debugging, selector review, accessibility snapshots, console errors, network issues, screenshots, and traces.

## Prerequisites

Playwright CLI is a command-line browser automation tool for coding agents. It provides
token-efficient browser control, accessibility snapshots, element refs, sessions, screenshots,
traces, console inspection, and network inspection.

Official docs:

- <https://playwright.dev/agent-cli/introduction>
- <https://playwright.dev/agent-cli/installation>
- <https://playwright.dev/agent-cli/snapshots>

Before use, verify:

```bash
node --version
playwright-cli --help
```

Use Node.js 20 or newer. When installation is needed and the user approves setup, install
the CLI with:

```bash
npm install -g @playwright/cli@latest
```

If the global command is unavailable, try:

```bash
npx playwright-cli --help
```

Do not install browsers, install packages, create persistent profiles, or authenticate into
external systems without user approval.

## Safety Constraints

- Do not modify repository files through browser automation.
- Do not run full test suites from this skill.
- Do not perform destructive or persistent live-environment actions.
- Do not store credentials or session data in project files.
- Prefer accessibility snapshots for structure and screenshots for visual-only evidence.
- Re-snapshot after navigation or state changes; element refs are valid only for the current snapshot.

## Procedure

Apply Safety Constraints throughout; if the requested browser action would violate them,
stop and report `blocked`.

1. Open the smallest relevant URL or local app state.
2. Capture an accessibility snapshot before interacting.
3. Interact only as much as needed to answer the QA question.
4. Inspect attributes, console output, network records, screenshots, or traces only when the snapshot is insufficient.
5. Label every live finding as `CONFIRMED_FROM_LIVE_UI` or `UNKNOWN`.
6. Close only sessions opened for the current task.

## Output Contract

Emit:

`Skill: qa-playwright-cli - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed`, `skipped`, or `blocked` |
| URL / Environment | Page or app inspected |
| Actions | Browser commands or flow performed |
| Findings | Findings labeled `CONFIRMED_FROM_LIVE_UI` or `UNKNOWN` |
| Evidence | Snapshot details, stable attributes, console/network facts, or artifact paths |
| Artifacts | Screenshot, trace, video, or snapshot paths, or `none` |
| Errors / Unknowns | Failed commands, missing access, unavailable credentials, or `none` |
