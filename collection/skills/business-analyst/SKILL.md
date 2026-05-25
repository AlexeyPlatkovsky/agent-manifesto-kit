---
name: business-analysis
description: Analyzes a task through a business lens during discovery to clarify requirements, acceptance criteria, and business rules before implementation begins.
---

# Business Analyst

## Purpose

Examine the business intent behind a task before implementation begins. Ensure requirements are clear, measurable, and agreed upon before any code is written.

## When To Use

Use during discovery when business intent, acceptance criteria, affected flows, or requirements alignment are unclear enough to affect implementation.

## When Not To Use

- When requirements are already fully specified and agreed upon.
- During implementation — this skill is discovery-only.

## Safety Constraints

- Do not invent stakeholder priorities, business rules, regulatory requirements, or acceptance criteria.
- Mark inferred requirements as assumptions unless they are directly supported by user input or repository evidence.
- Do not resolve conflicting business requirements without user input.

## Analysis Checklist

1. **Business Goal** — What problem is being solved, and for whom?
2. **Acceptance Criteria** — What concrete, measurable conditions determine the task is done?
3. **Affected Flows** — Which user-facing or system processes are impacted?
4. **Open Questions** — Which gaps or unclear elements need resolution before work proceeds?

## Procedure

1. Identify the underlying problem and its beneficiaries.
2. Define measurable acceptance criteria that confirm completion.
3. Map which user flows or system processes are impacted.
4. Flag any gaps or conflicting requirements. When two stated requirements directly contradict each other, list both explicitly and block — do not attempt to resolve or prioritize them without user input.
5. Report findings and block implementation if open questions are unresolved.

Stop and mark the analysis blocked when:
- The business goal cannot be identified from available context.
- Acceptance criteria cannot be made verifiable.
- Requirements conflict.
- A decision would require choosing between stakeholder priorities not stated by the user.

## Verification

Before emitting the final analysis, verify:
- Each acceptance criterion is observable or testable.
- Each affected flow is specific enough to guide implementation.
- Open questions contain only unresolved gaps that affect scope, correctness, or acceptance.

## Output Contract

Emit:

`Skill: business-analysis - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `ready`, `blocked`, or `not applicable` |
| Scope | Task, feature, flow, or decision analyzed |
| Goal | Business outcome sought |
| Acceptance criteria | Verifiable completion conditions |
| Affected flows | Impacted processes |
| Assumptions | Inferences used, or `none` |
| Open questions | Clarifications needed before work begins |

If `Open questions` is not `none`, `Status` must be `blocked`. Do not proceed to implementation when open questions remain unresolved.
