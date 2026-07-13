# Testing

## Strategy

Test the catalog and provider rules as focused behavior, then exercise adoption and CLI
handoffs through filesystem-backed tests. Keep the shipped product and its project-local
workshop boundary visible in manual checks.

## Test Levels

| Level | Scope | Tooling |
| --- | --- | --- |
| Unit | Catalog scanning, provider destinations, portability rules | Node test runner, compiled TypeScript |
| Integration | Adoption into temporary project roots, conflict behavior, bundle extras | Node test runner and filesystem fixtures |
| End-to-end | Built CLI commands and supported AI-CLI handoff paths | `npm test`; focused child-process tests |

## Running Feature Scenarios

Run `npm test` from the repository root. This builds TypeScript first and then runs the
Node test suite. Manual checks should use a temporary consumer project and confirm that
adoption writes only the provider target paths and expected bundle extras. Record feature
verification scenarios and evidence in the relevant Taskpilot feature item.

## Coverage Expectations

- Every supported capability type and bundle item is discoverable.
- Provider destinations and mechanical transforms are covered.
- Adoption covers clean targets, existing targets, `--force`, bundles, and bundle extras.
- AI-assisted adaptation covers the actionable prompt, complete file context, and child
  process invocation behavior; the corresponding evidence belongs in Taskpilot.
- Filtered list views cover the default catalog, exact lowercase selectors, bundle item
  summaries, empty results, invalid selectors, extra arguments, and unknown flags.

## Environments

- Local development: Node.js 20 or newer with dependencies installed via npm.
- CI/release: GitHub Actions using the workflow's pinned Node version, `npm ci`, and
  `npm test`.
- Adoption checks: isolated temporary directories representing consumer projects.

## Quality Gates

- TypeScript compilation succeeds.
- The full `npm test` command succeeds.
- Product-output changes keep `package.json`, `package-lock.json`, and `CHANGELOG.md`
  aligned unless release bookkeeping is explicitly deferred.
- Review confirms that workshop assets do not enter the runtime product catalog.
