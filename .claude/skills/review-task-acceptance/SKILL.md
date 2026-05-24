---
name: review-task-acceptance
description: Verifies that completed work satisfies the task's acceptance criteria, scope, and quality gates before sign-off. Use when the user asks to verify a task is done, accept a delivery, or check that a PR fulfills its ticket.
---

# Reviewing Task Acceptance

## When to use

The user wants to verify that finished work meets its spec before approving / closing / merging. Not for reviewing the spec itself (`review-task-specification`) or for code-level review (`review-code-correctness`).

## Inputs required

- The task / ticket spec with acceptance criteria
- The delivered artifact(s): PR, build, doc, design, deployed preview
- Required quality gates (CI, lint, tests, design review)

## Procedure

1. List every acceptance criterion from the spec.
2. For each AC, verify it against the delivered artifact:
   - Run the app, follow the steps, observe the result, OR
   - Inspect the relevant code / doc / design region
3. Record the verification method and outcome per AC.
4. Confirm scope boundary: nothing in "out of scope" was added; nothing in scope was silently dropped.
5. Check quality gates listed for the task.

## Acceptance matrix

```
| AC # | Criterion | Verification method | Evidence | Result |
| --- | --- | --- | --- | --- |
```

Result values: Pass / Fail / Partial / Not verifiable (with reason).

## Quality gates

Apply each gate when its trigger condition is met:

- CI build green — always
- Lint / type check clean — always
- Unit tests added or updated, passing — always when production code changed
- Integration / E2E tests for new behavior, passing — when the diff adds or changes a user-visible flow or an external integration
- Documentation updated (README, changelog, ADR, API docs) — when the diff changes public API, install/config steps, or architectural decisions
- Design review signed off — when the diff includes a UI change (HTML, JSX, native views, CSS)
- Accessibility / i18n checks — when the diff touches user-facing UI strings or interactive controls
- Security review — when the diff touches authentication, authorization, secrets, crypto, or input parsing
- Feature-flag / rollout plan stated — when the diff introduces a new flag, a new external dependency call, or a change behind a `// TODO: rollout` marker, or when the spec named the work as risky
- Migration / rollback plan — when the diff includes schema changes, data backfill, or irreversible deletions

## Scope check

- Diff size matches spec ambition (large unexpected diff → ask why)
- No unrelated refactors bundled in
- No dependencies added without spec mention or approval

## Output contract

- The acceptance matrix
- Quality gate results
- Scope check notes
- Verdict:
  - **Accept** — all ACs pass, gates green
  - **Accept with follow-ups** — minor issues tracked separately (list them)
  - **Reject** — at least one AC fails or a gate is red (list specifics)

## Stopping conditions

Stop and ask if:
- An AC cannot be verified without running an environment the user has not provided
- The delivered artifact and the spec are clearly mismatched (different feature)
- Evidence is missing for a destructive or irreversible step (migration, deletion)
