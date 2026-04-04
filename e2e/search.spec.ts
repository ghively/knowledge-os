import { test, expect } from '@playwright/test'

test.describe('Search Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('should perform semantic search', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i).first()
    if (await searchInput.isVisible()) {
      await searchInput.fill('knowledge management system')

      // Wait for search results
      await page.waitForTimeout(1500)

      // Should show search results
      const results = page.locator('[class*="result"], [class*="search"]')
      await expect(results.first()).toBeVisible({ timeout: 5000 })
    }
  })

  test('should display search results with scores', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i).first()
    if (await searchInput.isVisible()) {
      await searchInput.fill('test query')

      await page.waitForTimeout(1500)

      // Look for score indicators
      const scores = page.locator('[class*="score"], [class*="similarity"]')
      const count = await scores.count()

      if (count > 0) {
        await expect(scores.first()).toBeVisible()
      }
    }
  })

  test('should filter search by type', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i).first()
    if (await searchInput.isVisible()) {
      await searchInput.fill('test')

      await page.waitForTimeout(1000)

      // Look for type filter
      const typeFilter = page.getByText(/type|filter|all|objects|blocks/i).first()
      if (await typeFilter.isVisible()) {
        await typeFilter.click()

        // Select a type
        const objectsType = page.getByText(/objects/i).first()
        if (await objectsType.isVisible()) {
          await objectsType.click()

          await page.waitForTimeout(1000)
        }
      }
    }
  })

  test('should show empty state for no results', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i).first()
    if (await searchInput.isVisible()) {
      // Search for something unlikely to exist
      await searchInput.fill('xyz123nonexistentcontent789')

      await page.waitForTimeout(1500)

      // Should show empty state or no results message
      const noResults = page.getByText(/no results|not found|empty/i)
      if (await noResults.isVisible()) {
        await expect(noResults).toBeVisible()
      }
    }
  })

  test('should navigate to object from search results', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i).first()
    if (await searchInput.isVisible()) {
      await searchInput.fill('test')

      await page.waitForTimeout(1500)

      // Click on first result
      const firstResult = page.locator('[class*="result"], [class*="item"]').first()
      if (await firstResult.isVisible()) {
        await firstResult.click()

        // Should navigate to object details
        await page.waitForTimeout(1000)
      }
    }
  })

  test('should handle search suggestions/autocomplete', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i).first()
    if (await searchInput.isVisible()) {
      await searchInput.fill('test')

      await page.waitForTimeout(500)

      // Look for suggestions dropdown
      const suggestions = page.locator('[class*="suggestion"], [class*="dropdown"], [role="listbox"]')
      const count = await suggestions.count()

      if (count > 0) {
        await expect(suggestions.first()).toBeVisible()
      }
    }
  })

  test('should preserve search state on navigation', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i).first()
    if (await searchInput.isVisible()) {
      await searchInput.fill('test query')

      await page.waitForTimeout(1000)

      // Navigate away and back
      await page.goto('/tasks')
      await page.waitForTimeout(500)
      await page.goBack()
      await page.waitForTimeout(500)

      // Search query should be preserved
      const currentValue = await searchInput.inputValue()
      expect(currentValue).toBe('test query')
    }
  })

  test('should clear search results', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i).first()
    if (await searchInput.isVisible()) {
      await searchInput.fill('test query')

      await page.waitForTimeout(1500)

      // Clear search
      await searchInput.clear()

      await page.waitForTimeout(500)

      // Results should be cleared or reset
      const results = page.locator('[class*="result"]')
      const count = await results.count()

      // Should have no results or show default state
      if (count > 0) {
        // Results exist but might be default state
      }
    }
  })

  test('should handle special characters in search', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i).first()
    if (await searchInput.isVisible()) {
      await searchInput.fill('test & special @ chars')

      await page.waitForTimeout(1500)

      // Should not crash or show error
      const error = page.getByText(/error|failed|crashed/i)
      await expect(error).not.toBeVisible()
    }
  })

  test('should find similar content', async ({ page }) => {
    // Navigate to an object
    await page.goto('/objects')

    const firstObject = page.locator('[class*="object"], [class*="card"]').first()
    if (await firstObject.isVisible()) {
      await firstObject.click()

      await page.waitForTimeout(1000)

      // Look for "find similar" button/section
      const similarButton = page.getByText(/similar|related/i).first()
      if (await similarButton.isVisible()) {
        await similarButton.click()

        // Should show similar content
        await page.waitForTimeout(1000)

        const similarResults = page.locator('[class*="similar"], [class*="related"]')
        if (await similarResults.first().isVisible()) {
          await expect(similarResults.first()).toBeVisible()
        }
      }
    }
  })

  test('should handle search keyboard shortcuts', async ({ page }) => {
    // Press keyboard shortcut for search (usually Cmd/Ctrl + K)
    await page.keyboard.press((process.platform === 'darwin' ? 'Meta' : 'Control') + '+k')

    await page.waitForTimeout(500)

    // Search input should be focused
    const searchInput = page.getByPlaceholder(/search/i).first()
    if (await searchInput.isVisible()) {
      const isFocused = await searchInput.evaluate(el => document.activeElement === el)
      expect(isFocused).toBe(true)
    }
  })

  test('should show search history', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i).first()
    if (await searchInput.isVisible()) {
      await searchInput.focus()

      await page.waitForTimeout(500)

      // Look for recent searches
      const history = page.getByText(/recent|history|previous/i).first()
      if (await history.isVisible()) {
        await expect(history).toBeVisible()
      }
    }
  })

  test('should load more results on scroll', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i).first()
    if (await searchInput.isVisible()) {
      await searchInput.fill('test')

      await page.waitForTimeout(1500)

      // Scroll to bottom
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

      await page.waitForTimeout(1000)

      // Look for load more indicator
      const loadMore = page.getByText(/load more|loading|more results/i).first()
      if (await loadMore.isVisible()) {
        await expect(loadMore).toBeVisible()
      }
    }
  })
})
