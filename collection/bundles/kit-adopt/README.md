# Kit Adopt Bundle

The adoption helper for Agent Manifesto Kit. It installs a kit bundle or an individual
capability into a target project and wires it into that project's instruction entrypoint, so
consumers can adopt kit assets with minimal manual effort.

This is the "Part 2" of the kit: project-agnostic tooling that adapts the reusable
capabilities (such as the SDD bundle) to any project.

## Contents

| Item | Type | Path | Depends on |
| --- | --- | --- | --- |
| `kit-adopt` | skill | `skills/kit-adopt/` | `capability-portability` concept |
| `kit-adopt` | pipeline | `pipelines/kit-adopt.md` | `kit-adopt` skill |

## What it does

- Copies a selected bundle or item (plus declared dependencies) into the target's
  capability area, preserving internal structure so assets keep finding their
  required-environment files.
- Rewrites bundle-relative paths to the target layout and substitutes declared placeholders
  (project name, docs root) with consumer-provided values.
- Registers the installed capabilities in the target's instruction entrypoint
  (`AGENTS.md`, `CLAUDE.md`, or equivalent).
- Verifies the copied assets are portable and registered.

## How to copy

- Copy `collection/bundles/kit-adopt/` into your kit working area, then run the `kit-adopt`
  pipeline to install other bundles into a target project.
- The skill can also be used on its own for a single install without the detect/verify
  routing.
