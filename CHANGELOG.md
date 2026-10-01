# Changelog

All notable changes to this project are documented in this file.

Maintain this file as part of product or release-affecting work. Release automation publishes the version declared in `package.json`.

## 1.5.0 - 2026-10-01

### Added

- Added `agentkit update` to install `agent-manifesto-kit@latest` globally through npm,
  with streamed output, strict argument validation and propagated installation failures.
  Project capabilities continue to refresh through `agentkit sync`.

- Expanded `blender-3d` with a `blender-asset` entry skill and nested Quick, Standard and
  Production workflows. The full bundle syncs into Claude and Codex with no CLI changes.
- Added compact artifact/evidence handoffs, bounded repair reservations and per-phase usage
  records that distinguish unknown metrics from measured zero and identify parent/child calls.
- Added task-defined strict motion thresholds with coverage reporting, exact exported clip-set
  validation and optional mesh, skin and rig requirements.

### Changed

- Reference matching uses task-specific tolerances and identity checks instead of a universal
  silhouette score. Review effort and required views follow the chosen profile and changed scope.
- Retargeting chooses root displacement explicitly and applies pose offsets only to observed
  defects. Required missing evidence blocks acceptance; independent review is required for
  Production. Consumer projects retain machine paths, model choices and budgets.

### Fixed

- Package-content tests omit lifecycle scripts from their temporary manifests so npm 10
  cannot run Git hook setup outside a repository during `npm pack --dry-run`.
- Loop-seam checks sample fractional action endpoints precisely instead of rounding both to
  the same whole frame and potentially hiding a rotation discontinuity.

## 1.4.0 - 2026-10-01

### Added

- Added the public `session-retro` bundle: a digest-preparation skill and a read-only
  `retro-analyst` agent that reviews a finished Claude Code or Codex session and proposes at most
  five evidence-backed improvements (new or fixed scripts, skill pitfalls, project facts,
  removals). Approved changes use the consumer project's normal workflow. Its scripts summarize both tools' session logs
  (`session_digest.py`), provide one Stop hook for both tools that never blocks and nudges once
  per session when failure, repetition, inline-script, file-churn or correction thresholds are
  crossed (`retro_hook.py`), and register that hook in personal `.claude/settings.local.json`
  (or shared `.claude/settings.json` with `--shared`) and `.codex/hooks.json` (`install_hooks.py`).

### Changed

- Python bytecode caches are ignored so they cannot enter the repository or the package.

### Fixed

- `adopt` accepts `--provider=codex` as well as `--provider codex`. Missing option values,
  unknown adoption options and extra positional arguments fail before files are copied,
  instead of silently selecting the default Claude layout.
- Retro hook state stores derived pending-tool metadata without raw commands or request text,
  and resets counters when a transcript is truncated or replaced by a different path.
- Hook installation preserves unrelated scripts named `retro_hook.py` and rejects provider
  overrides among threshold flags. Digest detail is capped while signal totals remain exact.

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
