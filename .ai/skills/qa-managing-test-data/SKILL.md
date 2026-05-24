---
name: qa-managing-test-data
description: Designs deterministic, isolated test data setup and teardown for automated test suites using builders, factories, or API seeding. Use when the user asks how to seed data, create test fixtures, fix flaky data-dependent tests, or build data factories.
---

# Managing Test Data

## When to use

The user wants test data strategy or implementation — fixtures, builders, factories, API seeding, database snapshots — for an automated suite. Not for production data work.

## Inputs required

- Suite type (unit / integration / E2E / API)
- Existing data approach (none, fixtures, factories, DB dumps, API seeding)
- Persistence layer (in-memory, real DB, mocked service)
- Whether tests run in parallel

## Principles

- Each test owns the data it depends on.
- Prefer building data via the application's own API or domain factory over raw DB inserts.
- Data created by a test must be removed or scoped uniquely so parallel runs do not collide.
- No shared mutable fixtures across tests.
- Random fields default to deterministic seeds when assertions depend on them.

## Procedure

1. Classify the data need per test:
   - **Reference data** (countries, plans) — load once per suite, read-only
   - **Anchor data** (a known account for read-only assertions) — set up in suite setup
   - **Per-test data** (the user, order, record under test) — created in the test, torn down after
2. Pick the seeding mechanism, in priority order:
   - Domain factory / builder in the production codebase
   - REST/GraphQL seeding endpoint reserved for tests
   - Direct DB insert via a test-only repository
   - Raw SQL fixtures (last resort)
3. Apply the **builder pattern** for per-test data:
   - Sensible defaults for every field
   - Fluent overrides for the fields the test cares about
   - One `build()` that persists and returns the entity (or DTO)
4. Isolate runs:
   - Prefix or namespace generated identifiers with run ID / worker ID
   - Wrap integration tests in transactions that roll back when supported
   - Otherwise track created IDs and delete in teardown
5. Avoid randomness in assertions: seed faker / random sources per test.

## Quality checks

- No "magic" pre-existing row IDs hard-coded in tests.
- No `@Sql` scripts that depend on insertion order across files.
- Teardown runs even on test failure (try/finally, fixture finalizer, `afterEach`).
- Parallel-safe: two workers running the same test simultaneously do not collide.

## Output contract

- Files added / modified (builders, factories, fixtures, helpers)
- A short table: data category → mechanism → lifecycle
- Test command result demonstrating no flakes across 3 consecutive runs (when feasible)

## Stopping conditions

Stop if seeding requires production credentials or write access to a shared environment without isolation.
