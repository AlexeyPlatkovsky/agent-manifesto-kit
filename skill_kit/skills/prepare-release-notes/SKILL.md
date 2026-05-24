---
name: prepare-release-notes
description: Generates structured release notes by curating commits since the last release. Maintains the project's changelog file as the authoritative release record.
---

# Prepare Release Notes

## Purpose

Generate a structured release entry for the project's changelog file (commonly `CHANGES.md` or `CHANGELOG.md`) covering commits since the last release tag or version heading.

## Commit Filtering Rules

1. Start from the latest git tag or the most recent version heading in the changelog file.
2. Include only commits that modify meaningful product behavior.
3. Exclude: documentation-only commits, test-only commits, tooling and automation commits, and release preparation commits.
4. Include mixed commits when they contain relevant product changes alongside excluded content.

## Content Standards

- Use concise, user-facing language.
- Avoid raw commit hashes, author attributions, and internal implementation details.
- Group changes into categories — omit empty categories:
  - `Added` — new features or capabilities
  - `Changed` — changed behavior in existing features
  - `Fixed` — bug fixes
  - `Internal` — dependency bumps, refactors, or build changes

## Entry Format

```markdown
## [version] - YYYY-MM-DD

### Added
- ...

### Changed
- ...

### Fixed
- ...
```

Place the newest entry at the top of the changelog file.

## Pre-Release Gate

The changelog file must contain a non-empty version entry before release commands execute. A missing or empty version heading is a blocking issue.
