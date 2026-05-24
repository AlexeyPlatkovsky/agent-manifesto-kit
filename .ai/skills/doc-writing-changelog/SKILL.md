---
name: doc-writing-changelog
description: Writes a Keep-a-Changelog-style changelog entry grouped by Added / Changed / Fixed / Removed / Security from commits, PRs, or a diff range. Use when the user asks for a changelog, release notes, or CHANGELOG.md update.
---

# Writing a Changelog Entry

## When to use

The user wants a structured changelog entry for a release or version bump. Not for individual commit messages or PR descriptions.

## Inputs required

- Target version and release date
- Source of changes: tag/commit range (`git log v1.2.0..HEAD`), PR list, or merge log
- Audience: end users (most common) or internal contributors
- Existing CHANGELOG format if any — match it; if missing, default to Keep a Changelog

## Procedure

1. Collect changes from the source range. Read PR titles + bodies, not just commit subjects.
2. Filter:
   - Skip pure refactors, chores, CI tweaks, dependency bumps with no user impact (unless audience is contributors)
   - Skip reverted-then-redone work
   - Skip work entirely behind a disabled flag
3. Classify each remaining change into exactly one bucket:
   - **Added** — new user-facing capability
   - **Changed** — non-breaking change to existing behavior
   - **Deprecated** — still works, slated for removal
   - **Removed** — gone
   - **Fixed** — bug fix
   - **Security** — security-relevant fix
4. Rewrite each entry from the user's perspective:
   - Verb first ("Added X", "Fixed Y when Z")
   - One line, no jargon
   - Link to PR or issue
5. Sort within each bucket by impact, highest first.

## Entry format

```
## [<version>] - <YYYY-MM-DD>

### Added
- <Short user-visible description> ([#123](url))

### Changed
- …

### Fixed
- …

### Security
- …
```

## Breaking changes

If any change is breaking:
- Mark version bump as major (semver)
- Add a `### Breaking changes` block at the top of the version section
- Include migration steps or a link to a migration guide

## Quality checks

- No internal codenames or component paths in user-facing entries.
- No "various improvements" / "bug fixes" filler — name them.
- Each entry is independently understandable.
- Dates use ISO format.
- Versions follow the project's existing scheme.

## Output contract

- The changelog entry inserted at the top of the Unreleased / current version section
- Count of changes included vs filtered (with reasons for filtering category totals)

## Stopping conditions

Stop if the change range cannot be determined or if PR descriptions are missing for a non-trivial portion of changes.
