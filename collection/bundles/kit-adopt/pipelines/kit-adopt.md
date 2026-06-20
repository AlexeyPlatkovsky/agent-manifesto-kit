# Pipeline: Kit Adopt

## Purpose

Pre-defined routing plan for adopting one or more kit bundles or individual capabilities
into a target project. It detects the target's layout, installs the selected assets, and
verifies they are portable and registered.

This pipeline is a routing artifact. It sequences existing capabilities. It does not
implement step logic and does not emit its own output artifact.

## When to Apply

- The user wants to install a kit bundle (for example the SDD bundle) or specific
  capabilities into a consumer project.
- Skip when the user only wants to copy a single file by hand with no wiring.

## Inputs

- The kit source and the selection to install (bundle or items).
- The target repository root.
- Values for any placeholders the selected assets declare.

## Stages

| Stage | Capability | Required Visible Artifact |
| --- | --- | --- |
| 1. Detect | direct — locate the target's instruction entrypoint and capability area | none |
| 2. Select | direct — confirm the bundle or items to install and their dependencies | none |
| 3. Install | `Skill: kit-adopt` | `Skill: kit-adopt - output below` |
| 4. Offer companions | direct — present the installed bundle's `RECOMMENDS.md` companions; install any the user selects via `Skill: kit-adopt` | `Skill: kit-adopt - output below` for selected companions, or a note that none were selected |
| 5. Verify | direct, or `Agent: instruction-evaluator` when the target provides one | a portability/registration check result |

Skip stage 4 when the installed bundle has no `RECOMMENDS.md`. Do not advance past a stage
whose expected visible artifact is missing.

## Authority Sources

- the `capability-portability` concept (consumer-declared configuration only)
- each selected asset's declared Required Environment

## Stop Conditions

- No instruction entrypoint can be found in the target — stop and ask where capabilities
  should be registered.
- The install step reports a collision or missing dependency — resolve before verifying.
- Verification finds a copied asset still references kit-only paths — return to stage 3.

## Output Contract

The pipeline emits no artifact of its own. The install stage emits the `kit-adopt` skill
artifact, and the verify stage records its check result.
