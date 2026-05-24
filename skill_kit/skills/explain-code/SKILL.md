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

## Procedure

1. Start from the code that matters most to the question.
2. Trace the real control flow, data flow, and state transitions before discussing abstractions.
3. When code is incomplete or missing, use design docs to explain intended behavior and label it clearly as design intent, not implementation fact.
4. Include a small ASCII diagram when it clarifies ownership, lifecycle, or call flow.
5. Call out assumptions, extension points, or failure modes when relevant.

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
