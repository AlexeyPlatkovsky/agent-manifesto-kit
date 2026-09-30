# Changelog

All notable changes to this project are documented in this file.

Maintain this file as part of product or release-affecting work. Release automation publishes the version declared in `package.json`.

## 1.3.0 - 2026-09-30

### Added

- Added `agentkit ingest <path>` to import a skill folder, a Claude agent `.md`, or a Codex
  agent `.toml` into `collection/` (flat or `--bundle <name>`) in canonical form. Codex agents
  become Markdown agents with a read-only `tools:` list for read-only sandboxes and a `codex:`
  block for other settings.
- Added `agentkit sync` to keep hard copies of skills and agents in a project's native Claude
  (`.claude/skills`, `.claude/agents`) and Codex (`.agents/skills`, `.codex/agents/*.toml`)
  locations, tracked by `.agentkit-lock.json`: owned files update in place, local edits and
  unowned files are kept unless `--force`, dropped items and providers are removed, and
  `--dry-run` previews changes.
- Added the public `blender-3d` bundle: `blender-reference-model` and `blender-mocap-retarget`
  skills with tested Blender and image scripts, and a read-only `visual-reviewer` agent.

### Changed

- Boolean CLI flags (`--force`, `--replace`, `--dry-run`) no longer consume a following
  positional argument.
- A read-only Claude tool list is reported as translated to Codex `sandbox_mode` rather than
  dropped.
- The `kit-adopt` bundle names `AGENTS.md` (or the tool's equivalent root contract) as the
  instruction entrypoint instead of listing a Claude-specific file.

## 1.2.1 - 2026-09-30

### Fixed

- Fixed Codex adoption so Codex can discover adopted capabilities: skills are now written to
  `.agents/skills/<name>/` instead of `.codex/skills/`, and agents are rendered as native Codex
  TOML (`.codex/agents/<name>.toml` with `name`, `description`, `developer_instructions`)
  instead of Markdown. Read-only Claude tool lists map to `sandbox_mode = "read-only"`; an
  optional `codex:` frontmatter block supplies other Codex settings; other Claude-only keys are
  dropped with a warning. `.claude/skills/` and `.claude/agents/*.md` references are rewritten
  to the matching Codex locations.

## 1.2.0 - 2026-07-13

### Added

- Added exact lowercase `agentkit list skills`, `agentkit list agents`, and
  `agentkit list bundles` views while preserving the default full catalog.
- Added explicit validation for unsupported selectors, extra arguments, and unknown list
  options, plus stable empty-result behavior.

## 1.1.2 - 2026-07-10

### Fixed

- Fixed the release workflow by pinning the npm CLI upgrade to npm 11, preventing npm 12's newer Node engine requirement from breaking releases on the workflow's pinned Node version.

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
