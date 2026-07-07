# Changelog

All notable changes to this project are documented in this file.

Maintain this file as part of product or release-affecting work. Release automation publishes the version declared in `package.json`.

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
