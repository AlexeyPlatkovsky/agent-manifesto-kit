---
name: prepare-release-notes
description: Generates structured release notes by curating commits since the last release. Maintains the project's changelog file as the authoritative release record.
---

# Prepare Release Notes

## Purpose

Generate a structured release entry for the project's changelog file (commonly `CHANGES.md` or `CHANGELOG.md`) covering commits since the last release tag or version heading.

## Prerequisites

Before generating or editing release notes, confirm:
- The changelog file is identified and readable, or the user has approved the file to create.
- The release range has a clear baseline and upper bound.
- The target version and release date are known from user input, project release metadata, or existing changelog pattern.
- The commits in range can be inspected closely enough to distinguish product behavior from docs, tests, tooling, automation, and release-prep work.

If any item is missing, stop and ask only for the missing release input.

## Commit Filtering Rules

1. Start from the latest git tag or the most recent version heading in the changelog file.
2. Include only commits that modify meaningful product behavior.
3. Exclude: documentation-only commits, test-only commits, tooling and automation commits, and release preparation commits.
4. Include mixed commits when they contain relevant product changes alongside excluded content.
5. Use `Internal` only for release-relevant internal changes that affect shipped behavior, compatibility, security posture, or operator-visible release behavior. Otherwise, exclude dependency, refactor, and build-only commits.

## Safety Constraints

- Do not create, move, delete, or rewrite git tags.
- Do not run release, publish, version bump, commit, or push commands.
- Do not include uncommitted work unless the user explicitly requested draft notes from the working tree.
- Do not invent user-facing impact from commit messages alone when the diff does not support it.
- Do not include secrets, credentials, private URLs, or internal incident details in release notes.

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

### Internal
- ...
```

Place the newest entry at the top of the changelog file.

Omit empty categories, including `Internal`.

## Output Contract

Emit:

`Skill: prepare-release-notes - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed`, `drafted`, or `blocked` |
| Changelog File | File updated, proposed, or `none` |
| Release | Version and date, or `unknown` |
| Range | Baseline and upper bound used |
| Changed Files | Changelog file changed, or `none` |
| Assumptions | Inferences used, or `none` |
| Excluded Commits | Count or short reason summary |
| Blockers | Remaining blockers, or `none` |

Then include the formatted changelog entry per the Entry Format above.

## Stop Conditions

- If no git history exists, stop and ask the user what release range or commit to use as the baseline.
- If no git tags exist and no version heading is present in the changelog, stop and ask the user what version number and baseline to use before generating the entry.
- If no changelog file exists (no `CHANGES.md`, `CHANGELOG.md`, or equivalent), stop and ask the user what filename and location to use before creating it.
- Stop and report the release notes as blocked when git tags and changelog version headings disagree about the latest release baseline.
- Stop and report blocked when multiple changelog files appear authoritative.
- Stop and report blocked when the target version or release date cannot be determined.
- Stop and report blocked when no eligible product changes remain after filtering commits.
- Stop and report blocked when an entry for the target version already exists and replacing or merging it was not explicitly approved.

## Verification

Before reporting completion, verify:
- The newest non-empty release entry is at the top of the changelog.
- The version, date, and release range match the intended release.
- Every included bullet is supported by an eligible commit or diff.
- Empty categories are omitted.
- Existing changelog entries were not reordered or rewritten unintentionally.

## Pre-Release Gate

The changelog file must contain a non-empty version entry before release commands execute. A missing or empty version heading is a blocking issue.
