---
name: explain-code
description: Explains how code works by tracing actual implementations and execution paths. Use when teaching the codebase or answering "how does this work?" questions about implemented code.
---

# Explain Code

## When To Use

Use when the question is about how code actually works — tracing flow, understanding data transformations, or mapping component relationships.

## When Not To Use

- When the answer can be found in documentation without reading the code.
- For design or planning questions before implementation exists — label those as design intent, not code behavior.

## Prerequisites

Before explaining code, confirm:
- The question identifies a module, behavior, entry point, file, symbol, or flow to inspect.
- The relevant implementation files can be read.
- The explanation can be grounded in implementation evidence, not only names, docs, tests, or assumptions.

If the target is unclear, ask the smallest clarifying question or state the chosen scope before explaining.

## Safety Constraints

- Do not present design intent, documentation, test expectations, or naming conventions as implemented behavior unless the implementation confirms it.
- Do not invent missing control flow, data transformations, defaults, side effects, or error handling.
- Do not reveal secrets, credentials, private keys, or sensitive environment values discovered while reading code.

## Procedure

1. Start from the code that matters most to the question.
2. Trace the real control flow, data flow, and state transitions before discussing abstractions.
3. When code is incomplete or missing, use design docs to explain intended behavior and label it clearly as design intent, not implementation fact.
4. Include a small ASCII diagram when it clarifies ownership, lifecycle, or call flow.
5. Call out assumptions, extension points, or failure modes when relevant.

When several entry points or flows could answer the question, choose the one most directly matching the user's wording and state that scope. If two or more choices are equally plausible and would produce different explanations, stop and ask for clarification.

Stop and report the explanation as blocked when:
- The target implementation cannot be located or read.
- The behavior depends on missing generated code, runtime configuration, external service behavior, or unavailable files.
- Multiple plausible flows exist and choosing one would materially change the answer.
- Documentation and code conflict, and the implementation cannot be verified.

## Verification

Before emitting the explanation, verify:
- Each behavior claim is supported by a code reference or clearly labeled as an inference.
- Entry points, terminal effects, and key state changes are included when relevant.
- Any docs-based explanation is labeled as design intent when implementation evidence is absent or conflicting.

## Output Contract

Emit:

`Skill: explain-code - output below`

Then include:

| Field | Content |
| --- | --- |
| Status | `completed`, `partial`, or `blocked` |
| Scope | Code area, symbol, flow, or behavior explained |
| Sources Read | Files, symbols, docs, or runtime evidence inspected |
| Assumptions | Inferences used, or `none` |
| Unknowns | Missing or unverified areas, or `none` |

Use `partial` or `blocked` when important behavior cannot be verified from implementation evidence. Then deliver the explanation using the default structure below when status is not `blocked`.

## Default Structure

1. **What it is** — one or two sentences describing the module, component, or subsystem role.
2. **Entry points** — which route, command, function, or event starts the behavior.
3. **How it flows** — step-by-step execution path with file references.
4. **Key collaborators** — which modules, stores, or boundaries it depends on.
5. **Gotchas** — common misunderstandings, hidden state, lifecycle rules, or failure modes.

## Style Rules

- Use analogies only when they simplify the explanation; do not force them.
- Do not invent behavior not visible in the code. Label inferences as inferences.
- Prefer concrete file, function, and symbol references over generic commentary.
- Keep ASCII diagrams compact.
- Separate implemented behavior from design-doc behavior when they differ.
