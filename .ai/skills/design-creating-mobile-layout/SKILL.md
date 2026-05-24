---
name: design-creating-mobile-layout
description: Creates a native mobile screen layout in Pencil.dev for iOS or Android with platform-appropriate components, safe areas, and gesture targets. Use when the user asks to design an iOS or Android app screen, or a mobile-first product surface.
---

# Creating a Mobile Layout

## When to use

The user wants a native mobile-app screen design. For responsive web screens use `design-creating-web-layout`. For design tokens use `design-creating-design-system`.

## Tool constraint

`.pen` files are accessed only through `pencil` MCP tools.

## Inputs required

- Platform (iOS, Android, or both)
- Device targets (default iOS: iPhone 15; Android: Pixel 8) plus a small device (iPhone SE, small Pixel)
- Primary user action on this screen
- Existing design system tokens

## Procedure

1. Open the document and fetch `pencil:get_variables` and `pencil:get_guidelines`.
2. Create a frame at the primary device size. Mark safe-area insets:
   - iOS: top status bar 44–59 pt, home indicator 34 pt at bottom
   - Android: status bar 24 dp, gesture nav inset 16 dp
3. Apply the platform navigation pattern:
   - iOS: large title or compact navigation bar; tab bar 49 pt
   - Android: top app bar 56 dp; bottom navigation 80 dp (Material 3)
4. Build content with auto-layout, single column, token-based spacing.
5. Tap targets: minimum 44×44 pt (iOS HIG) / 48×48 dp (Material).
6. Typography uses platform-aware text styles from the system (San Francisco / Roboto / project equivalent token).
7. Add small-device variant by reflowing the same frame — no redesign.
8. Mark gestures and transitions in notes; do not draw them as layout.
9. Snapshot and screenshot for review.

## Platform-specific checks

**iOS**
- Back navigation uses chevron + label or system back gesture
- Modal vs push correctly chosen
- System icons from SF Symbols token set

**Android**
- FAB placement respects bottom inset
- Snackbar / toast areas reserved above nav
- Material icons from token set

## Quality checks

- All spacing on the token scale
- One primary action visible without scroll
- Empty / loading / error states defined or explicitly deferred
- Dark-mode variant defined or explicitly deferred
- Text legible at minimum body size for the platform
- No critical action in the thumb-unfriendly zone (top corners on phones)

## Output contract

- Frame IDs per device and per platform
- Components used
- New tokens introduced (should be zero)
- Notes on gestures, transitions, accessibility deferred

## Stopping conditions

Stop if:
- Platform is unspecified and the user has not picked one
- Required system components are missing from the library
- Interaction behavior is needed but undefined
