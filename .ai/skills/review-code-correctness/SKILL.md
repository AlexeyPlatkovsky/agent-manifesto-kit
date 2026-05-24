---
name: review-code-correctness
description: Reviews a code diff for correctness bugs — logic errors, edge cases, error handling, concurrency, and resource leaks. Use when the user asks for a code review, PR review, diff review, or correctness check that is not specifically about security or performance.
---

# Reviewing Code for Correctness

## When to use

The user wants a correctness-focused review of a diff or PR. For security-focused review, use `review-code-security`. For performance, use `review-code-performance`.

## Inputs required

- The diff to review (PR URL, branch comparison, or staged diff)
- The change's stated intent (PR description, ticket, or user explanation)

If intent is unstated, ask before reviewing — a review without intent is just opinion.

## Procedure

1. Read the diff in full, then the stated intent. Confirm the diff matches the intent.
2. For each changed file, evaluate against the checklist below.
3. Group findings by severity. Cite file:line for every finding.
4. Distinguish facts from opinions.

## Correctness checklist

**Logic**
- Off-by-one in loops, ranges, slices
- Boundary conditions (empty, single, max)
- Inverted conditions, mixed up arguments
- Dead branches, unreachable code
- Floating-point comparison, integer overflow
- Timezone, locale, encoding assumptions
- Date math across DST and leap years

**Error handling**
- Caught exceptions that should bubble; bubbled ones that should be caught
- Errors silently swallowed (empty catch, ignored return codes)
- Partial failure recovery (retries, idempotency)
- Resource cleanup on exception paths (try/finally, context managers, defer)

**Concurrency**
- Shared mutable state without synchronization
- Race conditions in init/teardown
- Deadlock potential from lock ordering
- Async functions not awaited; sync code blocking the event loop

**State and data**
- Mutation of inputs the caller still owns
- Null/undefined deref
- Stale cache invalidation
- Schema migrations missing or non-reversible

**API contract**
- Public signature changes without deprecation
- Behavior change not reflected in tests or docs
- New required config without defaults

**Tests**
- Tests added/changed match production change
- Negative cases covered
- No tests removed without justification

## Severity

- **Blocking**: incorrect behavior, data loss risk, broken contract
- **Major**: edge case unhandled, missing test for risky logic
- **Minor**: style, naming, comment, small clarity issue
- **Nit**: cosmetic only — mark explicitly

## Output contract

```
| Severity | File:line | Finding | Suggested fix |
| --- | --- | --- | --- |
```

End with a verdict: Approve / Approve with comments / Request changes / Block.

## Stopping conditions

Stop and ask if:
- The diff is too large to review in one pass (suggest splitting)
- Intent is unstated
- Required context (linked spec, ADR) is missing
