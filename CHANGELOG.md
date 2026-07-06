# Changelog

All notable changes to this project are documented in this file.

Maintain this file as part of product or release-affecting work. Release automation may also update it from Conventional Commits when changes land on `main`.

## 1.1.0 - 2026-07-06

### Added

- Added the `qa-automation` bundle with QA test creation, test debugging, Playwright CLI, exploration, review, and verification capabilities.

### Changed

- Updated project documentation for the released post-1.0 workflow and ongoing feature development.
- Updated the release workflow to use the semantic-release 25 plugin line with npm trusted publishing through GitHub Actions OIDC.
- Removed the semantic-release release-commit step so protected `main` is not updated outside pull requests.

## 1.0.0 - 2026-06-20

### Added

- Published the initial stable `agent-manifesto-kit` package to npm.
