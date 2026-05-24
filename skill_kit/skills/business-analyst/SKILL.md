---
name: business-analyst
description: Analyzes a task through a business lens during discovery to clarify requirements, acceptance criteria, and business rules before implementation begins.
---

# Business Analyst

## Purpose

Examine the business intent behind a task before implementation begins. Ensure requirements are clear, measurable, and agreed upon before any code is written.

## When To Use

Use during the discovery phase of any task to ensure the work is well-defined and stakeholder alignment is confirmed.

## When Not To Use

- When requirements are already fully specified and agreed upon.
- During implementation — this skill is discovery-only.

## Analysis Checklist

1. **Business Goal** — What problem is being solved, and for whom?
2. **Acceptance Criteria** — What concrete, measurable conditions determine the task is done?
3. **Affected Flows** — Which user-facing or system processes are impacted?
4. **Open Questions** — Which gaps or unclear elements need resolution before work proceeds?

## Procedure

1. Identify the underlying problem and its beneficiaries.
2. Define measurable acceptance criteria that confirm completion.
3. Map which user flows or system processes are impacted.
4. Flag any gaps or conflicting requirements.
5. Report findings and block implementation if open questions are unresolved.

## Output Contract

Emit:

`Skill: business-analyst - output below`

Then include:

| Field | Content |
| --- | --- |
| Goal | Business outcome sought |
| Acceptance criteria | Verifiable completion conditions |
| Affected flows | Impacted processes |
| Open questions | Clarifications needed before work begins |

Do not proceed to implementation when open questions remain unresolved.
