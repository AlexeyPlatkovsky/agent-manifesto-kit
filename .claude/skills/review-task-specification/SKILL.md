---
name: review-task-specification
description: Reviews a task or user-story specification for clarity, testability, scope, dependencies, and readiness to implement. Use when the user asks to review a ticket, story, requirements doc, or task spec before work starts.
---

# Reviewing a Task Specification

## When to use

The user wants a pre-implementation review of a written task spec, ticket, or story. Not for reviewing completed work (`review-task-acceptance`) or code (`review-code-correctness`).

## Inputs required

- The spec text (ticket, doc, or file path)
- Audience (engineer, agent, designer)
- Any linked source-of-truth (PRD, design, ADR)

## Review checklist

**Goal**
- Stated in one sentence
- User-visible or system-visible, not vague ("improve UX")

**Why**
- Reason exists and cites a source: metric, bug, request, dependency
- Urgency is justified or absent (not "ASAP" with no reason)

**Scope**
- Clear list of what is in scope
- Explicit out-of-scope items (at least one)
- No hidden adjacent work assumed

**Acceptance criteria**
- Each is testable (someone could write a test against it)
- Given / When / Then or equivalent observable form
- Cover happy path AND at least one negative / boundary case
- No "should be fast" / "should be intuitive" without measurable target

**Dependencies and inputs**
- All external dependencies named (APIs, designs, accounts, approvals)
- Pre-conditions for work to start are listed
- Decisions required upstream are flagged, not assumed

**Risks**
- Honest list of unknowns
- Each risk has a mitigation or a plan to investigate

**Non-functionals**
- Performance / security / accessibility / i18n flagged if relevant
- Compliance or legal constraints called out

**Ownership and timing**
- Owner identified
- Deadline or target date if relevant
- Reviewer / approver named

## Severity

- **Blocking**: spec cannot be safely implemented as written (missing AC, undefined dependency, contradiction)
- **Major**: significant ambiguity likely to cause rework
- **Minor**: clarity / wording / formatting
- **Info**: suggestion

## Output contract

```
| Severity | Area | Finding | Suggested fix |
```

End with a readiness verdict:
- **Ready** — implementation can begin
- **Needs info** — specific gaps to fill (list them)
- **Blocked** — depends on an unmade decision or unavailable input
- **Split required** — too large; propose split points

## Stopping conditions

Stop if the linked source-of-truth (PRD, design) is unavailable — flag and request before completing the review.
