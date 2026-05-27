# NOTICE

This collection contains skills and agents derived in part from third-party open-source work. The attributions below cover those derivations. Original authors retain copyright over their original work; derivative content in this collection is provided under the same license terms unless explicitly relicensed.

## frontend-polish

- **Source:** `impeccable` skill by Philipp Bakaus — https://github.com/pbakaus/impeccable
- **License:** Apache License 2.0
- **Upstream attribution:** `impeccable` is itself derived from Anthropic's `frontend-design` skill.
- **Nature of derivation:** Distilled from the upstream skill's shared design laws and the `polish` sub-command reference. Routing, sub-command system, loader scripts, `pin`/`unpin` machinery, and the `npx impeccable` runtime dependency are not carried over. Behavioral checklist and AI-slop patterns are adapted and rewritten for this collection's single-file skill format.

## frontend-design

- **Sources:**
  - `frontend-design` skill by Anthropic — https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md
  - `impeccable` skill by Philipp Bakaus — https://github.com/pbakaus/impeccable (specifically the `shape` / `craft` sub-command lineage and shared design laws)
- **License:** Apache License 2.0 for `impeccable`; license terms for Anthropic's skill per its repository LICENSE.txt.
- **Nature of derivation:** Generative aesthetic guidance distilled from the Anthropic upstream and the `impeccable` shape/craft references. Routing, sub-commands, loader scripts, and runtime dependencies are not carried over. Procedure, design laws, AI-slop list, and output contract are rewritten for this collection's single-file skill format.

## frontend-audit

- **Source:** `impeccable` skill by Philipp Bakaus — https://github.com/pbakaus/impeccable (specifically the `audit` sub-command reference)
- **License:** Apache License 2.0
- **Nature of derivation:** Diagnostic checklist adapted from the `audit` sub-command, rewritten as a guide-only single-file skill. WCAG criterion references are independently verifiable; no upstream tool-invocation or script content is carried over.
