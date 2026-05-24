---
name: qa-reporting-bugs
description: Writes a clear, reproducible bug report with environment, steps, actual vs expected results, and severity. Use when the user describes a defect, asks to file a bug, or wants help structuring a found issue for a tracker.
---

# Reporting a Bug

## When to use

The user has discovered or describes a defect and wants a properly structured report suitable for a bug tracker (Jira, Linear, GitHub Issues, etc.).

## Inputs required

- One-line problem description
- How it was observed (which test case, exploratory session, user report)
- Environment (build version, OS, browser/device, region, account/role)
- Reproduction steps (or available evidence)

If the user has not actually reproduced the issue themselves, mark the report as "needs reproduction" and request confirmation.

## Procedure

1. Confirm reproduction at least twice. If not reproducible, stop and follow the Stopping conditions below.
2. Strip the steps to the minimum sequence that triggers the bug.
3. Capture evidence: screenshot, video, console log, network trace, request/response, server log lines with timestamps.
4. Classify severity and priority using the project's existing scale. If the project has no defined scale, stop and ask the user to confirm one before filing.

## Bug report template

```
Title: <component> — <symptom> when <trigger>
Severity: S1 | S2 | S3 | S4
Environment:
  - Build / version:
  - OS / browser / device:
  - User / role / region:
  - Date / time observed (with timezone):
Preconditions:
  - <required state>
Steps to reproduce:
  1.
  2.
Expected:
  - <what should happen, with source: spec, ACs, prior behavior>
Actual:
  - <what happens, including error text verbatim>
Reproducibility: Always | Intermittent (X/Y) | Once
Evidence:
  - <links to screenshots, videos, logs>
Workaround:
  - <if known>
Notes:
  - <recent related changes, suspected area>
```

## Quality checks

- Title is specific, not "X doesn't work".
- Steps are minimal and complete — a stranger could follow them.
- "Expected" cites a source (requirement, doc, prior behavior).
- Error messages are pasted verbatim, not paraphrased.
- No personally identifying information in evidence.

## Output contract

- The completed bug report
- A one-line triage hint (suggested component, suspected owner if obvious)

## Stopping conditions

Stop and ask if reproduction is not confirmed or if evidence cannot be safely shared (PII, secrets).
