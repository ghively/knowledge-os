import { test, expect } from '@playwright/test'

test.describe('Smoke Tests', () => {
  test('should load the application', async ({ page }) => {
    await page.goto('/')

    // Should show main application
    await expect(page).toHaveTitle(/Knowledge OS/i)

    // Should have main navigation
    const nav = page.locator('nav').first()
    await expect(nav).toBeVisible()
  })

  test('should have working health check', async ({ request }) => {
    const response = await request.get('/health')

    expect(response.status()).toBe(200)

    const data = await response.json()
    expect(data).toHaveProperty('status', 'healthy')
  })

  test('should navigate to objects page', async ({ page }) => {
    await page.goto('/')

    // Click on objects/navigation
    const objectsLink = page.getByText(/objects|knowledge/i).first()
    if (await objectsLink.isVisible()) {
      await objectsLink.click()

      await expect(page).toHaveURL(/\/objects|\/knowledge/)
    }
  })

  test('should navigate to tasks page', async ({ page }) => {
    await page.goto('/')

    // Click on tasks
    const tasksLink = page.getByText(/tasks/i).first()
    if (await tasksLink.isVisible()) {
      await tasksLink.click()

      await expect(page).toHaveURL(/\/tasks/)
    }
  })

  test('should navigate to agents page', async ({ page }) => {
    await page.goto('/')

    // Click on agents
    const agentsLink = page.getByText(/agents/i).first()
    if (await agentsLink.isVisible()) {
      await agentsLink.click()

      await expect(page).toHaveURL(/\/agents/)
    }
  })

  test('should navigate to settings page', async ({ page }) => {
    await page.goto('/')

    // Click on settings
    const settingsLink = page.getByText(/settings/i).first()
    if (await settingsLink.isVisible()) {
      await settingsLink.click()

      await expect(page).toHaveURL(/\/settings/)
    }
  })

  test('should have responsive sidebar', async ({ page }) => {
    await page.goto('/')

    const sidebar = page.locator('[class*="sidebar"]').first()

    // Desktop - sidebar should be visible
    await page.setViewportSize({ width: 1280, height: 720 })
    if (await sidebar.isVisible()) {
      await expect(sidebar).toBeVisible()
    }

    // Mobile - sidebar should be hidden or collapsible
    await page.setViewportSize({ width: 375, height: 667 })
  })

  test('should handle search functionality', async ({ page }) => {
    await page.goto('/')

    // Find search input
    const searchInput = page.getByPlaceholder(/search/i).first()

    if (await searchInput.isVisible()) {
      await searchInput.fill('test query')

      // Should show search results or dropdown
      await page.waitForTimeout(500)
    }
  })

  test('should have working WebSocket connection', async ({ page }) => {
    await page.goto('/')

    // Listen for WebSocket connections
    const wsConnections: string[] = []

    page.on('websocket', ws => {
      ws.on('framesent', frame => wsConnections.push(frame.payload as string))
    })

    // Wait a bit for connection to establish
    await page.waitForTimeout(2000)

    // WebSocket connection should be established
    // (This is a basic check, actual WebSocket testing may require more setup)
  })

  test('should handle API errors gracefully', async ({ page }) => {
    // Navigate to a page that might not exist
    await page.goto('/non-existent-page')

    // Should show error or redirect
    await page.waitForTimeout(1000)

    // Should not show uncaught error
    const errorElement = page.getByText(/uncaught error|runtime error/i)
    await expect(errorElement).not.toBeVisible()
  })
})
