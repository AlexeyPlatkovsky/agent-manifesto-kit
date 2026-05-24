---
name: qa-writing-playwright-tests
description: Writes Playwright end-to-end tests in TypeScript or Python using role-based locators, auto-waiting, and project fixtures. Use when the user asks for Playwright tests, E2E browser tests, or @playwright/test specs.
---

# Writing Playwright Tests

## When to use

The user wants Playwright tests. For Selenium, use `qa-writing-selenium-tests`. For page objects, use `qa-building-page-objects`.

## Inputs required

- Language (TypeScript or Python)
- Whether project uses `@playwright/test` or `pytest-playwright`
- Existing fixtures and config (`playwright.config.*`)
- Auth strategy (storage state, login flow, API seed)

## Procedure

1. Read existing tests and `playwright.config` to match conventions (projects, baseURL, retries, reporters).
2. Add tests to the existing folder. Name files `<feature>.spec.ts` or `test_<feature>.py`.
3. Use locator priority:
   - `getByRole(...)` with accessible name
   - `getByLabel`, `getByPlaceholder`, `getByText` for forms / content
   - `getByTestId` for opaque components
   - CSS / XPath only when no semantic option exists
4. Rely on Playwright's auto-waiting. Use `expect(locator).toHaveText(...)` style assertions, not `waitForTimeout`.
5. Network and state:
   - Prefer API setup over UI clicks for preconditions
   - Reuse `storageState` for authenticated sessions
   - Use `page.route` to mock only what is necessary
6. Each `test()` is independent. Group with `describe` only for shared `beforeEach` of pure setup.
7. For traces and videos, rely on config (`trace: 'on-first-retry'`); do not enable per test.
8. Run `npx playwright test --reporter=line` (or pytest equivalent) and confirm green.

## Quality checks

- No `page.waitForTimeout`.
- No locators built from substring text in untranslated apps.
- Soft assertions only when verifying multiple independent properties in one screen state.
- Tests use `test.step` for non-trivial flows so traces are readable.
- No `console.log` left in committed tests; use `test.info().annotations` if metadata is needed.

## Output contract

- Files added / modified
- Locators chosen and rationale
- Test command and result
- New fixtures or config changes (explicit)

## Stopping conditions

Stop and ask if:
- Auth setup is undefined
- The flow needs a network mock that touches third-party billing or payment
- A new project / browser target would be added to config
