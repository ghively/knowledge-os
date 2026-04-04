# Knowledge OS E2E Test Suite

This directory contains end-to-end tests using Playwright.

## Test Structure

- `playwright.config.ts` - Playwright configuration
- `smoke.spec.ts` - Basic smoke tests for critical functionality
- `objects.spec.ts` - E2E tests for objects CRUD
- `tasks.spec.ts` - E2E tests for task management
- `search.spec.ts` - E2E tests for search functionality

## Running Tests

First, install Playwright:

```bash
npm install -D @playwright/test
npx playwright install
```

Run all E2E tests:

```bash
npx playwright test
```

Run tests in headed mode (see browser):

```bash
npx playwright test --headed
```

Run specific test file:

```bash
npx playwright test smoke.spec.ts
```

Run tests in debug mode:

```bash
npx playwright test --debug
```

View test report:

```bash
npx playwright show-report
```

## Test Configuration

E2E tests are configured in `playwright.config.ts`:

- Runs against http://localhost:5173
- Tests on Chromium, Firefox, and WebKit
- Starts dev server automatically
- Takes screenshots on failures
- Records traces on retry

## Requirements

Before running E2E tests, ensure:

1. Backend server is running on port 8000
2. Frontend dev server is available (will be started automatically)
3. No authentication is required for basic tests

## Writing E2E Tests

```typescript
import { test, expect } from '@playwright/test'

test('should do something', async ({ page }) => {
  await page.goto('/')

  const button = page.getByText('Click me')
  await button.click()

  await expect(page).toHaveURL('/success')
})
```

## Notes

- E2E tests test the full application stack
- Tests are slower than unit/integration tests
- Use page object model for complex interactions
- Always wait for elements before interacting
- Use data-testid attributes for more stable selectors
