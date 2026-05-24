---
name: design-reviewing-ui
description: Reviews a UI screen or flow from screenshots or a running app against usability heuristics and accessibility standards. Use when the user asks for a UI/UX heuristic review, design critique, or accessibility audit of a screenshot, running app, or deployed URL. Not for `.pen` files — use `pencil-auditing-design`.
---

# Reviewing UI

## When to use

The user wants a critique of an existing design provided as screenshots, image attachments, or a running app / URL. For structural audit of a `.pen` file (tokens, components, naming), use `pencil-auditing-design` instead. For code review, use `review-code-correctness`.

## Inputs required

- The artifact to review: screenshot(s), image attachment, or URL
- Audience and primary user goal on the screen
- Platform (web, iOS, Android)

If the user references a `.pen` file, stop and route to `pencil-auditing-design`.

## Heuristic checklist

Walk Nielsen's heuristics, adapted, then add accessibility:

1. **Visibility of system status** — loading, progress, success, error states are present and discoverable.
2. **Match with real world** — wording matches user vocabulary; no internal jargon.
3. **User control and freedom** — back, cancel, undo are reachable from any irreversible step.
4. **Consistency and standards** — components reused, not redrawn; platform conventions respected.
5. **Error prevention** — destructive actions require confirmation; constraints stated up front.
6. **Recognition over recall** — relevant info visible; users not asked to remember from a prior screen.
7. **Flexibility and efficiency** — shortcuts / power-user paths exist where the task is repeated.
8. **Aesthetic and minimalist design** — one primary action per screen; no decorative clutter.
9. **Help users recognize / diagnose / recover from errors** — error text explains what + why + next step.
10. **Help and documentation** — contextual help where the action is non-obvious.

## Accessibility checklist

- Color contrast: body text ≥ 4.5:1, large text ≥ 3:1 (flag pairs that look risky; do not assert exact ratios without measurement)
- Tap target ≥ 44×44 pt / 48×48 dp
- Focus order is logical; visible focus state on every interactive element
- Form fields have visible labels (placeholders are not labels)
- Icon-only buttons have accessible names
- Motion can be reduced (no required animation to complete a task)
- Critical info not conveyed by color alone

## Visual checks

- Spacing on the project's scale
- Type uses defined styles only
- Alignment grid consistent across siblings
- Hierarchy: primary action draws the eye first

## Output contract

```
| Severity | Heuristic / Check | Frame or region | Finding | Suggested fix |
```

Severities: Blocking, Major, Minor, Nit.

End with:
- Top 3 issues to fix first
- Verdict: Ship / Ship with fixes / Hold

## Stopping conditions

Stop if:
- The user goal for the screen is unknown
- The artifact is incomplete (single static frame for a multi-state interaction)
- Accessibility checks require runtime tooling not available here
