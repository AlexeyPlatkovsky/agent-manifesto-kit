---
id: feat-adopt
title: adopt command
status: done
parent: sdd/archive/01_agentkit-mvp/epic.md
---

## User story

As a consumer, I want to copy a capability into my project for my AI provider with one command.

## Acceptance criteria (EARS)

- When the user runs `agentkit adopt <name>`, the system shall copy the capability to the provider-correct location and print the destination and wiring step.
- Where `--provider` is omitted, the system shall default to `claude`.
- If `<name>` is unknown or ambiguous, then the system shall exit non-zero with a clear message and write nothing.
- If the target path already exists, then the system shall refuse to overwrite and exit non-zero.

## Tasks

`tasks/02_adopt-command/` — 001 adopt command + providers.
