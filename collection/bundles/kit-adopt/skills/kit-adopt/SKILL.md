---
name: kit-adopt
description: Installs a kit bundle or an individual capability into a target project — copies the assets into the target's capability area, rewrites bundle-relative paths and declared placeholders to the target, and registers the capabilities in the target's instruction entrypoint. Use when adopting kit assets into a consumer project.
---

## Scope

- Install a selected source: a whole bundle, or one skill/agent/pipeline plus its declared
  dependencies.
- Copy the assets into the target's capability area, adapt them to the target, and register
  them so the target's tooling can discover them.
- Do not modify unrelated target files, source code, or assets the user did not select.

## Required Environment

- The kit source tree containing the bundle or item to install.
- A target project with an instruction entrypoint (for example `AGENTS.md`, `CLAUDE.md`, or
  an equivalent root contract) and a capability area to receive the assets.
- The `capability-portability` concept: copied assets work in the target after consumer-
  declared configuration (paths, project vocabulary) is supplied, without other source edits.

## Inputs

- Source selection: bundle path or item path(s) in the kit.
- Target repository root and the capability area to install into.
- Values for any placeholders the assets declare (project name, docs root, etc.).

## Procedure

Apply the Stop Conditions throughout; halt and report when any is met.

1. Confirm the source selection and resolve its declared dependencies; confirm the target
   root, capability area, and instruction entrypoint.
2. Copy the assets into the target, preserving each bundle's internal structure so that
   assets keep finding their required-environment files (conventions, templates).
3. Rewrite bundle-relative references to match where the assets now live in the target.
4. Substitute declared placeholders with the consumer-provided values. Leave undeclared
   project-specific content untouched.
5. Register the installed capabilities in the target's instruction entrypoint under its
   capability registry or equivalent list. If the entrypoint has no such section, add a
   clearly labeled one rather than inventing routing rules.
6. If the installed source declares recommended companions (a `RECOMMENDS.md`), surface them
   as optional follow-ups for the user to accept or decline. Do not auto-install them;
   install only the ones the user selects, through this same skill.
7. Report what was installed, rewritten, registered, and surfaced.

## Stop Conditions

Stop and report a blocker when:
- the target instruction entrypoint cannot be found or is ambiguous;
- installing would overwrite an existing target asset (report the collision; do not
  overwrite without confirmation);
- the source selection or a declared dependency cannot be located.

## Output Contract

Emit:

`Skill: kit-adopt - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed`, `blocked`, or `skipped` |
| Installed | Assets copied, with target paths |
| Dependencies | Dependencies pulled in, or `none` |
| Rewrites | Path and placeholder substitutions applied |
| Registry | Entrypoint edits made to register the capabilities |
| Companions surfaced | Optional companions offered from the source's `RECOMMENDS.md`, or `none` |
| Collisions | Existing target assets that blocked install, or `none` |
| Blockers | Unresolved issues, or `none` |
