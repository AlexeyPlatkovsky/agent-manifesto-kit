---
name: playwright-cli
description: Automates browser interactions for live UI exploration, testing, form filling, screenshots, and data extraction. Use when direct browser interaction is needed to answer questions that repository files cannot.
---

# Playwright CLI

## What Is Playwright CLI

`playwright-cli` is a command-line tool for browser automation built on [Playwright](https://playwright.dev) (Microsoft's browser testing framework). It is invoked as a bash command and controls real browsers (Chrome, Firefox, WebKit, Edge) to navigate pages, interact with elements, capture screenshots, and inspect live UI state.

## Prerequisites

`playwright-cli` must be available as a bash command in your environment. If it is not installed, stop and ask the user to set it up before continuing.

A typical setup:
```bash
npm install -g playwright
npx playwright install chromium   # install browser binaries
```

Verify it is available:
```bash
playwright-cli --version
```

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

Store generated files in designated directories rather than the repository root:

| Type | Directory |
| --- | --- |
| Snapshots | `.playwright/snapshots/` |
| Screenshots | `.playwright/screenshots/` |
| Traces | `.playwright/traces/` |
| Videos | `.playwright/videos/` |
| Fixtures | `.playwright/fixtures/` |

## Safety Rules

- Do not modify source files via browser automation.
- Do not store credentials in session files or artifacts.
- Do not run full test suites — use targeted, minimal interactions.
- Do not perform destructive actions on live environments.

## Evidence Reporting

- Mark all live UI findings as `CONFIRMED_FROM_LIVE_UI`.
- Include supporting evidence: accessible names, text labels, stable attributes, or artifact paths.
- If browser access or credentials are unavailable, record the finding as `UNKNOWN`.
