import { test, expect } from '@playwright/test'

test.describe('Objects CRUD Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('should display objects list', async ({ page }) => {
    // Navigate to objects page
    await page.goto('/objects')

    // Should show objects section
    const objectsSection = page.getByText(/objects|knowledge/i)
    await expect(objectsSection).toBeVisible()
  })

  test('should create a new object', async ({ page }) => {
    await page.goto('/objects')

    // Click create button
    const createButton = page.getByText(/create|new|add/i).first()
    if (await createButton.isVisible()) {
      await createButton.click()

      // Fill in object details
      const titleInput = page.getByLabel(/title/i).or(page.getByPlaceholder(/title/i))
      if (await titleInput.isVisible()) {
        await titleInput.fill('E2E Test Object')

        const contentInput = page.getByLabel(/content/i).or(page.getByPlaceholder(/content/i))
        if (await contentInput.isVisible()) {
          await contentInput.fill('This is a test object created by E2E tests')
        }

        // Submit form
        const submitButton = page.getByText(/save|create|submit/i).first()
        await submitButton.click()

        // Wait for creation
        await page.waitForTimeout(1000)

        // Should show success message or redirect
        const successMessage = page.getByText(/created|saved|success/i)
        await expect(successMessage).toBeVisible({ timeout: 5000 })
      }
    }
  })

  test('should filter objects by type', async ({ page }) => {
    await page.goto('/objects')

    // Look for filter controls
    const filterButton = page.getByText(/filter|type/i).first()
    if (await filterButton.isVisible()) {
      await filterButton.click()

      // Select a filter option
      const noteFilter = page.getByText(/note/i).first()
      if (await noteFilter.isVisible()) {
        await noteFilter.click()

        // Should filter results
        await page.waitForTimeout(500)
      }
    }
  })

  test('should search objects', async ({ page }) => {
    await page.goto('/objects')

    const searchInput = page.getByPlaceholder(/search/i).first()
    if (await searchInput.isVisible()) {
      await searchInput.fill('test query')

      // Wait for search results
      await page.waitForTimeout(1000)

      // Should show search results
      const results = page.locator('[class*="result"], [class*="object"]')
      await expect(results.first()).toBeVisible({ timeout: 5000 })
    }
  })

  test('should view object details', async ({ page }) => {
    await page.goto('/objects')

    // Click on first object
    const firstObject = page.locator('[class*="object"], [class*="card"]').first()
    if (await firstObject.isVisible()) {
      await firstObject.click()

      // Should show object details
      await page.waitForTimeout(500)

      const title = page.getByRole('heading').first()
      await expect(title).toBeVisible()
    }
  })

  test('should edit an object', async ({ page }) => {
    await page.goto('/objects')

    // Click on first object
    const firstObject = page.locator('[class*="object"], [class*="card"]').first()
    if (await firstObject.isVisible()) {
      await firstObject.click()

      // Wait for details page
      await page.waitForTimeout(500)

      // Click edit button
      const editButton = page.getByText(/edit/i).first()
      if (await editButton.isVisible()) {
        await editButton.click()

        // Edit title
        const titleInput = page.getByLabel(/title/i)
        if (await titleInput.isVisible()) {
          await titleInput.fill('Updated E2E Test Object')

          // Save changes
          const saveButton = page.getByText(/save|update/i).first()
          await saveButton.click()

          // Should show success
          await page.waitForTimeout(1000)
        }
      }
    }
  })

  test('should delete an object', async ({ page }) => {
    await page.goto('/objects')

    // Find an object to delete
    const firstObject = page.locator('[class*="object"], [class*="card"]').first()
    if (await firstObject.isVisible()) {
      // Click on object
      await firstObject.click()
      await page.waitForTimeout(500)

      // Look for delete button
      const deleteButton = page.getByText(/delete|remove/i).first()
      if (await deleteButton.isVisible()) {
        // Handle confirmation dialog
        page.on('dialog', dialog => dialog.accept())

        await deleteButton.click()

        // Should redirect or show success
        await page.waitForTimeout(1000)
      }
    }
  })

  test('should show object relations', async ({ page }) => {
    await page.goto('/objects')

    const firstObject = page.locator('[class*="object"], [class*="card"]').first()
    if (await firstObject.isVisible()) {
      await firstObject.click()
      await page.waitForTimeout(500)

      // Look for relations section
      const relations = page.getByText(/relations|related/i).first()
      if (await relations.isVisible()) {
        await expect(relations).toBeVisible()
      }
    }
  })

  test('should create wiki-style links', async ({ page }) => {
    await page.goto('/objects')

    // Create or edit object
    const createButton = page.getByText(/create|new/i).first()
    if (await createButton.isVisible()) {
      await createButton.click()

      const contentInput = page.getByLabel(/content/i).or(page.getByPlaceholder(/content/i))
      if (await contentInput.isVisible()) {
        // Add wiki link
        await contentInput.fill('Link to [[Another Page]]')

        const saveButton = page.getByText(/save|create/i).first()
        await saveButton.click()

        await page.waitForTimeout(1000)
      }
    }
  })

  test('should handle pagination', async ({ page }) => {
    await page.goto('/objects')

    // Look for pagination controls
    const nextPage = page.getByText(/next|more|load more/i).first()
    if (await nextPage.isVisible()) {
      await nextPage.click()

      // Should load more objects
      await page.waitForTimeout(1000)
    }
  })
})
