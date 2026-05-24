---
name: doc-writing-readme
description: Writes or updates a project README with overview, install, usage, and contribution sections grounded in actual repo state. Use when the user asks for a README, project overview doc, or top-level documentation refresh.
---

# Writing a Project README

## When to use

The user asks for a new or updated README at the project root or for a subpackage. Not for architecture decisions (`doc-writing-architecture-decision`) or changelog entries (`doc-writing-changelog`).

## Inputs required

- Project root path
- Audience (open-source users, internal contributors, end users)
- Language / runtime / package manager

Inspect the repo first: `package.json`, `pyproject.toml`, `pom.xml`, `Cargo.toml`, top-level scripts. Do not invent facts.

## Required sections

In order:

1. **Title and one-line purpose**
2. **Status badges** — include a badge only if its source exists in the repo:
   - Build badge: include if `.github/workflows/*.yml`, `.gitlab-ci.yml`, `.circleci/`, or `azure-pipelines.yml` is present
   - Version badge: include if the package is published (npm `name` in package.json, `[project] name` in pyproject.toml + a `version`, etc.)
   - License badge: include if a `LICENSE` file is present at the repo root
   - Coverage badge: include only if a coverage service config (`codecov.yml`, `.coveragerc` + service) is present
3. **What it does** — 2–4 sentences, no marketing
4. **Requirements** — runtime versions, OS, external services
5. **Install** — exact commands, copy-pasteable
6. **Quick start** — minimal working example
7. **Usage** — common operations (build, test, run, lint)
8. **Configuration** — environment variables and config files with defaults
9. **Project layout** — top-level directories explained in one line each
10. **Contributing** — link to CONTRIBUTING.md if present; otherwise a short paragraph
11. **License** — name only, link to LICENSE file

Omit a section only if no truthful content exists for it; do not pad.

## Quality checks

- Every command is verifiable from repo files (scripts, manifests).
- No "coming soon", "TBD", or placeholder fillers.
- No version numbers hard-coded that will drift (link to releases page instead).
- Links use relative paths within the repo.
- Code blocks declare a language.
- No emoji unless the existing project uses them.

## Procedure

1. Inspect manifests, scripts, CI config, and 1–2 entry-point files.
2. Draft each section above using only verified facts.
3. For unknowns, list them at the end as "Open questions" and ask the user.
4. Confirm any destructive change (overwriting existing README) before writing.

## Output contract

- The README content
- A short diff summary if updating an existing file
- List of facts asserted with their source file

## Stopping conditions

Stop if:
- Repo state cannot be inspected
- An existing README would be overwritten without user approval
- Critical facts (license, install steps) cannot be verified
