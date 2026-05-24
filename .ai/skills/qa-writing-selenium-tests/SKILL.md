---
name: qa-writing-selenium-tests
description: Writes Selenium WebDriver UI tests in Java or Python with stable locators, explicit waits, and page-object usage. Use when the user asks for Selenium tests, WebDriver tests, or browser automation in a Selenium-based project.
---

# Writing Selenium Tests

## When to use

The user wants Selenium-based browser tests. For Playwright, use `qa-writing-playwright-tests`. For page-object scaffolding, use `qa-building-page-objects`.

## Inputs required

- Language (Java or Python — match project)
- Test framework (JUnit 5 / TestNG / pytest)
- Selenium version (4.x recommended)
- Browser targets and where they run (local, Grid, cloud provider)
- Whether the project already has page objects

## Procedure

1. Read 1–2 existing tests and one page object to match conventions.
2. Add the test to the existing suite directory; do not create a parallel suite.
3. Locator strategy, in priority order:
   - `data-testid` or equivalent stable test attribute
   - `id` if guaranteed unique and stable
   - Accessible name (`By.cssSelector("[aria-label='…']")`)
   - CSS selectors with semantic anchors
   - XPath only when the above are not feasible
   - Never: nth-child positional chains, absolute XPath, text in non-default locale
4. Use explicit waits (`WebDriverWait` + `ExpectedConditions`). Never `Thread.sleep` / `time.sleep`.
5. One test verifies one behavior. Setup goes in `@BeforeEach` / fixture; teardown closes drivers reliably.
6. Manage WebDriver lifecycle through the project's existing factory; do not instantiate `new ChromeDriver()` in tests.
7. Make tests independent — no order dependencies, no shared mutable state.
8. Run the suite headed locally first; then headless in CI mode.

## Quality checks

- No sleeps, no polling loops with arbitrary intervals.
- Locators centralized in page objects, not inline strings.
- Assertions use the project's assertion library (AssertJ / Hamcrest / pytest assert).
- Screenshot on failure is wired through existing listener / fixture, not added per test.
- No hard-coded environment URLs — read from config.

## Output contract

- Files added / modified
- Locators used and why each was chosen
- Command run and pass/fail
- Any page-object additions

## Stopping conditions

Stop and ask if:
- Stable locators are unavailable (request `data-testid` from devs)
- The flow requires authentication state not yet captured
- Test would need a new dependency
