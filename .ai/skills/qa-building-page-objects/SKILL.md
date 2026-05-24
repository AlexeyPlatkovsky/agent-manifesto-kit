---
name: qa-building-page-objects
description: Designs and implements Page Object or Component Object classes for UI automation in Selenium or Playwright projects. Use when the user asks to add a page object, refactor inline locators into POM, or scaffold page classes for a new screen.
---

# Building Page Objects

## When to use

The user wants to introduce or extend Page Object Model (POM) classes for a UI suite. Not for writing tests themselves (`qa-writing-selenium-tests`, `qa-writing-playwright-tests`).

## Inputs required

- Automation framework (Selenium / Playwright)
- Language (Java / Python / TypeScript)
- Existing POM layout (if any) — match it
- Pages / components in scope

## Principles

- One class per page or major component.
- Page object exposes **actions** (verbs) and **queries** (read-only state), never raw locators.
- Locators are private fields/constants inside the class.
- No assertions inside page objects; assertions live in tests.
- No waits exposed to callers — page objects encapsulate readiness.
- Constructors take only what is needed: driver/page handle, base URL, and dependencies.

## Procedure

1. Map the screen: list user-visible regions and the actions a test would take.
2. For each region, decide page vs component:
   - **Page** = a routable URL or full-screen view
   - **Component** = a reusable region (header, dialog, table row)
3. Create the class in the existing POM folder, following naming convention (`LoginPage`, `CartItemComponent`).
4. Define private locators using the framework's stable strategy (`data-testid`, role-based, etc.).
5. Expose actions as methods returning either `void`, the same page (for chaining), or the next page navigated to.
6. Expose queries that return primitives or DTOs, never raw `WebElement` / `Locator`.
7. Add a single `isLoaded()` / `waitUntilReady()` method that callers can use, encapsulating wait logic.
8. Update or add 1–2 tests that consume the new page object to prove it works.

## Quality checks

- No `Thread.sleep` / `waitForTimeout` inside page objects.
- No conditional logic that branches on UI state inside actions (split into separate methods instead).
- No cross-page knowledge: `LoginPage` does not know about `DashboardPage` internals — it returns it as a type.
- Locators are not duplicated across pages.

## Output contract

- Files created/modified
- Public method list per new class
- Tests updated to use the new POM
- Test run result

## Stopping conditions

Stop if the screen requires a locator strategy not yet stable (request `data-testid` from devs first).
