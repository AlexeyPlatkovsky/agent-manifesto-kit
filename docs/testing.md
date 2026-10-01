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
- Ingest covers skill folders, Claude agents, Codex TOML agents, bundle targets, canonical
  path rewriting, duplicate and name-clash refusal, and missing descriptions.
- Sync covers native layouts for both providers, the lock file, update-in-place, local-edit and
  unowned-file protection, `--force`, item and provider removal, and `--dry-run`.
- Bundle scripts with logic of their own are tested from the Node suite: the `session-retro`
  digest, Stop hook and installer run against synthetic Claude Code and Codex logs (skipped
  when `python3` is unavailable). Coverage includes private pending-tool state, partial/truncated
  logs, bounded summaries, native adoption/sync, executed hook wrappers, default/shared settings,
  preview, installation/removal, unrelated-hook preservation and invalid threshold flags.
- Adoption option parsing covers space/equals provider forms and rejects malformed arguments
  before writing. Package preview checks that Python bytecode is excluded from `collection/`.
  Temporary packaging fixtures retain the real manifest's package-selection fields but omit
  lifecycle scripts: npm 10.8.2 runs `prepare` during pack despite `--ignore-scripts`, and these
  fixtures intentionally have no Git repository for the hook-configuration command.
- Filtered list views cover the default catalog, exact lowercase selectors, bundle item
  summaries, empty results, invalid selectors, extra arguments, and unknown flags.

## CLI Update Validation

`test/update.test.js` runs the built CLI against isolated fake npm executables. It covers fixed
global/latest arguments, inherited output, failure exit codes, missing npm, interruption,
argument rejection and non-mutating help/version. Tests perform no real global install or
registry request. Windows uses an npm `.cmd` shim; the POSIX signal-specific test is skipped
there. Actual registry access and global write permissions remain installation-environment concerns.

## Blender Bundle Validation

The Blender tests cover task-state evidence invalidation, repair ceilings, unknown/duplicate
usage, exact export requirements, provider sync and nested workflow packaging. Python script
tests use `python3`; Blender fixture tests use `BLENDER` or an executable on `PATH`. Run
`BLENDER=/path/to/blender npm test` to include actual headless motion/export fixtures; without
Blender those tests are reported as skipped. A release validation claiming Blender coverage
must record its version and run those fixtures. The 1.5.0 local validation uses Blender 5.2.1 LTS.

Record Node/npm versions and Blender availability with test totals. For the 1.5.0 suite,
Blender availability produces 99 passing tests; without Blender, its parent test is skipped
and the 11 nested cases are not registered, producing 87 passes and one skip (88 total).
The original CI failure used Node 20.20.2/npm 10.8.2; the initial local pass used
Node 24.18.0/npm 11.16.0. A pass on one toolchain does not establish a pass on the other.

Instruction evaluation and scenario acceptance review test the five changed instruction
artifacts separately from script execution. Neither these tests nor the audit establish a
specific percentage saving or quality equivalence between model/effort presets.

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
