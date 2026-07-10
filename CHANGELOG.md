# Changelog

All notable changes to this project are documented in this file.

Maintain this file as part of product or release-affecting work. Release automation publishes the version declared in `package.json`.

## 1.1.1 - 2026-07-10

### Fixed

- Fixed `agentkit adopt --cli` so copied capabilities are actually adapted in target projects: Codex now runs with a writable sandbox and no approval prompts (`--sandbox workspace-write --ask-for-approval never`) instead of inheriting a read-only, proposal-only sandbox; the adaptation prompt now uses explicit approval/action language so it is treated as an actionable task rather than context; Claude Code now receives the prompt over stdin instead of argv so large prompts no longer risk hitting OS argument-length limits; copied bundle extras (e.g. SDD templates) are now included in the adaptation file list.

## 1.1.0 - 2026-07-07

### Added

- Added the `qa-automation` bundle with QA test creation, test debugging, Playwright CLI, exploration, review, and verification capabilities.

### Changed

- Updated project documentation for the released post-1.0 workflow and ongoing feature development.
- Updated the release workflow to publish the exact version declared in `package.json` with npm trusted publishing through GitHub Actions OIDC.
- Added npm duplicate-version checks and GitHub release creation for the matching `v<version>` tag.
- Removed semantic-release from release automation so protected `main` is not updated outside pull requests.

## 1.0.0 - 2026-06-20

### Added

- Published the initial stable `agent-manifesto-kit` package to npm.
