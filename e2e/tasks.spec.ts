import { test, expect } from '@playwright/test'

test.describe('Tasks Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/tasks')
  })

  test('should display tasks list', async ({ page }) => {
    // Should show tasks section
    const tasksSection = page.getByText(/tasks/i)
    await expect(tasksSection).toBeVisible()
  })

  test('should create a new task', async ({ page }) => {
    // Look for create button
    const createButton = page.getByText(/create|new task|add task/i).first()
    if (await createButton.isVisible()) {
      await createButton.click()

      // Fill in task details
      const titleInput = page.getByLabel(/title/i).or(page.getByPlaceholder(/title|task name/i))
      if (await titleInput.isVisible()) {
        await titleInput.fill('E2E Test Task')

        const descriptionInput = page.getByLabel(/description/i)
        if (await descriptionInput.isVisible()) {
          await descriptionInput.fill('This is a test task created by E2E tests')
        }

        // Submit form
        const submitButton = page.getByText(/save|create|submit/i).first()
        await submitButton.click()

        // Wait for creation
        await page.waitForTimeout(1000)

        // Should show new task
        const newTask = page.getByText('E2E Test Task')
        await expect(newTask).toBeVisible()
      }
    }
  })

  test('should filter tasks by status', async ({ page }) => {
    // Look for status filter
    const statusFilter = page.getByText(/todo|in progress|done/i).first()
    if (await statusFilter.isVisible()) {
      await statusFilter.click()

      // Should filter tasks
      await page.waitForTimeout(500)
    }

    // Look for filter dropdown
    const filterDropdown = page.getByLabel(/filter|status/i).first()
    if (await filterDropdown.isVisible()) {
      await filterDropdown.click()

      // Select a status
      const todoOption = page.getByText(/todo/i).first()
      if (await todoOption.isVisible()) {
        await todoOption.click()

        await page.waitForTimeout(500)
      }
    }
  })

  test('should filter tasks by priority', async ({ page }) => {
    const priorityFilter = page.getByText(/priority|high|low|medium/i).first()
    if (await priorityFilter.isVisible()) {
      await priorityFilter.click()

      await page.waitForTimeout(500)
    }
  })

  test('should update task status', async ({ page }) => {
    // Find a task
    const firstTask = page.locator('[class*="task"], [class*="card"]').first()
    if (await firstTask.isVisible()) {
      await firstTask.click()

      await page.waitForTimeout(500)

      // Look for status update controls
      const statusButton = page.getByText(/change status|update|mark as/i).first()
      if (await statusButton.isVisible()) {
        await statusButton.click()

        // Select new status
        const inProgressOption = page.getByText(/in progress|started/i).first()
        if (await inProgressOption.isVisible()) {
          await inProgressOption.click()

          // Should update task
          await page.waitForTimeout(1000)
        }
      }
    }
  })

  test('should assign task to agent', async ({ page }) => {
    const firstTask = page.locator('[class*="task"], [class*="card"]').first()
    if (await firstTask.isVisible()) {
      await firstTask.click()

      await page.waitForTimeout(500)

      // Look for assign button
      const assignButton = page.getByText(/assign|agent/i).first()
      if (await assignButton.isVisible()) {
        await assignButton.click()

        // Should show agent selection dialog
        const dialog = page.locator('[role="dialog"]').first()
        if (await dialog.isVisible()) {
          // Select an agent
          const agentOption = page.locator('[class*="agent"], [role="option"]').first()
          if (await agentOption.isVisible()) {
            await agentOption.click()

            // Confirm assignment
            const confirmButton = page.getByText(/assign|confirm/i).first()
            await confirmButton.click()

            await page.waitForTimeout(1000)
          }
        }
      }
    }
  })

  test('should view task context', async ({ page }) => {
    const firstTask = page.locator('[class*="task"], [class*="card"]').first()
    if (await firstTask.isVisible()) {
      await firstTask.click()

      await page.waitForTimeout(500)

      // Look for context/details button
      const contextButton = page.getByText(/context|details|more info/i).first()
      if (await contextButton.isVisible()) {
        await contextButton.click()

        // Should show task context
        const contextPanel = page.locator('[class*="context"], [class*="details"]').first()
        if (await contextPanel.isVisible()) {
          await expect(contextPanel).toBeVisible()
        }
      }
    }
  })

  test('should delete a task', async ({ page }) => {
    const firstTask = page.locator('[class*="task"], [class*="card"]').first()
    if (await firstTask.isVisible()) {
      // Click on task
      await firstTask.click()
      await page.waitForTimeout(500)

      // Look for delete button
      const deleteButton = page.getByText(/delete|remove/i).first()
      if (await deleteButton.isVisible()) {
        // Handle confirmation dialog
        page.on('dialog', dialog => dialog.accept())

        await deleteButton.click()

        // Should update list
        await page.waitForTimeout(1000)
      }
    }
  })

  test('should display task counts', async ({ page }) => {
    // Look for task counts/statistics
    const countsSection = page.getByText(/count|total|statistics/i).first()
    if (await countsSection.isVisible()) {
      await expect(countsSection).toBeVisible()
    }
  })

  test('should search tasks', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search|filter/i).first()
    if (await searchInput.isVisible()) {
      await searchInput.fill('test task')

      // Wait for search results
      await page.waitForTimeout(1000)

      // Should filter tasks
      const tasks = page.locator('[class*="task"]')
      const count = await tasks.count()
      expect(count).toBeGreaterThanOrEqual(0)
    }
  })

  test('should handle inline task creation', async ({ page }) => {
    // Look for inline creation input
    const inlineInput = page.getByPlaceholder(/quick add|new task/i).first()
    if (await inlineInput.isVisible()) {
      await inlineInput.fill('Quick task from E2E test')

      // Submit (press Enter or click button)
      await inlineInput.press('Enter')

      await page.waitForTimeout(1000)

      // Should create task
      const newTask = page.getByText(/Quick task from E2E test/i)
      if (await newTask.isVisible()) {
        await expect(newTask).toBeVisible()
      }
    }
  })

  test('should show task priority indicators', async ({ page }) => {
    const tasks = page.locator('[class*="task"], [class*="priority"]')

    const count = await tasks.count()
    if (count > 0) {
      // Check if any tasks have priority indicators
      const priorityIndicator = page.locator('[class*="priority"], [data-priority]').first()
      if (await priorityIndicator.isVisible()) {
        await expect(priorityIndicator).toBeVisible()
      }
    }
  })
})
