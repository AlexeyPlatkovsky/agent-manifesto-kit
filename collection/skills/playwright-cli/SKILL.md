---
name: playwright-cli
description: Automates browser interactions for live UI exploration, testing, form filling, screenshots, and data extraction. Use when direct browser interaction is needed to answer questions that repository files cannot.
---

# Playwright CLI

## What Is Playwright CLI

`playwright-cli` is a command-line tool for browser automation built on [Playwright](https://playwright.dev) (Microsoft's browser testing framework). It is invoked as a bash command and controls real browsers (Chrome, Firefox, WebKit, Edge) to navigate pages, interact with elements, capture screenshots, and inspect live UI state.

## Prerequisites

Before using `playwright-cli`, confirm:
- Node.js 20 or newer is available.
- `playwright-cli` is available globally or through `npx`.
- `playwright-cli --help` or `npx playwright-cli --help` succeeds.
- Required browsers are available, or can be installed with `playwright-cli install-browser`.

A typical setup:
```bash
npm install -g @playwright/cli@latest
playwright-cli --help
playwright-cli install-browser
```

If the command is not available, stop and ask the user to set it up before continuing.

## When To Use

Use for live browser automation when repository files, docs, and tests cannot reliably answer the current question.

Prefer repository evidence first. Run browser commands only when the codebase does not have the answer.

## Core Capabilities

- Navigate to URLs
- Click, double-click, type, fill forms, hover, drag, check/uncheck elements
- Take screenshots and capture accessibility snapshots
- Evaluate JavaScript expressions
- Inspect element attributes and DOM state
- Read console logs and network requests
- Manage named sessions, multiple tabs, and persistent browser profiles
- Mock and route network requests
- Record traces and videos for debugging
- Support multiple browser types: Chrome, Firefox, WebKit, Edge

## Artifact Organization

Store generated artifacts in the CLI output directory. By default, `playwright-cli` writes generated files such as snapshots and screenshots under `.playwright-cli/`; projects may override this with `outputDir` in `.playwright/cli.config.json` or `PLAYWRIGHT_MCP_OUTPUT_DIR`.

When an artifact is part of the final evidence, use an explicit `--filename` when the command supports it.

## Safety Rules

- Do not modify source files via browser automation.
- Do not store credentials in session files or artifacts.
- Do not run full test suites — use targeted, minimal interactions.
- Do not perform destructive actions on live environments.
- Before any state-changing interaction, confirm the target URL/environment is intended and the action is necessary for the user's request.
- Do not submit purchases, delete data, send messages, change permissions, or mutate live production data unless the user explicitly approved that exact action.
- Do not use authentication, persistent profiles, saved sessions, or stored credentials unless explicitly approved.

## Interaction Rules

- Use the smallest targeted browser flow that can answer the question.
- Avoid long command chains without observing state between steps.
- Use refs from the latest accessibility snapshot for interactions whenever possible.
- Re-snapshot after navigation, submissions, or major UI state changes because refs are only valid for the current snapshot.
- Use selectors or locators only when refs are unavailable or insufficient, and state that choice in the evidence.

## Verification

Before reporting completion, verify:
- The final page state was captured with a snapshot or screenshot.
- Claims about visual layout, canvas, charts, or non-accessible UI are supported by screenshots.
- Claims about text, controls, and forms are supported by accessibility snapshot evidence when available.
- Any console or network finding names the command used and the observed result.

## Output Contract

Emit:

`Skill: playwright-cli - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed`, `partial`, or `blocked` |
| URL / Environment | Page or app visited, including local/remote context when known |
| Session / Profile | Session name, profile mode, or `default in-memory` |
| Actions | Targeted steps performed |
| Findings | Each finding labeled `CONFIRMED_FROM_LIVE_UI` or `UNKNOWN` |
| Evidence | Snapshot excerpts, accessible names, stable refs/attributes, console/network facts, or artifact paths |
| Artifacts | Screenshot, snapshot, trace, video, or PDF paths, or `none` |
| Errors / Unknowns | Failed commands, missing access, unavailable credentials, or `none` |

## Error Handling

When a browser command fails (page not found, element not found, timeout, JS error):
- If the failure may be caused by stale refs after navigation or page change, take one fresh snapshot and retry once only for non-destructive actions.
- Do not retry destructive, submitting, purchasing, deleting, or permission-changing actions without explicit user approval.
- Record unresolved failures as `UNKNOWN` with the command, error reason, and available evidence.
- Continue with any remaining independent actions.

## Evidence Reporting

- Mark all live UI findings as `CONFIRMED_FROM_LIVE_UI`.
- Include supporting evidence: accessible names, text labels, stable attributes, or artifact paths.
- If browser access or credentials are unavailable, record the finding as `UNKNOWN`.
