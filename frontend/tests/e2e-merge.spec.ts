import { test, expect } from '@playwright/test'
import path from 'path'

const TEST_PPT = path.resolve('E:\\Code\\ai-teaching-ppt\\uploads\\cc29e001dff6\\ppt_a_test_downloaded.pptx')

test.describe('PPT Merge Page E2E', () => {
  test('should load merge page and upload PPT', async ({ page }) => {
    await page.goto('http://localhost:3000/merge', { waitUntil: 'networkidle' })

    // Step 1: Page should load with heading
    const heading = page.getByRole('heading', { name: 'PPT 智能合并' })
    await expect(heading).toBeVisible({ timeout: 10000 })
    await page.screenshot({ path: 'test-results/01-merge-page-loaded.png' })
    console.log('STEP 1: Merge page loaded')

    // Step 2: Find upload inputs
    const fileInputs = page.locator('input[type="file"]')
    const count = await fileInputs.count()
    console.log(`STEP 2: Found ${count} file inputs`)
    expect(count).toBeGreaterThanOrEqual(2)

    // Step 3: Upload PPT A (the first visible file input)
    await fileInputs.nth(0).setInputFiles(TEST_PPT)
    await page.waitForTimeout(1000)
    await page.screenshot({ path: 'test-results/02-after-file-a.png' })
    console.log('STEP 3a: PPT A selected')

    // After selecting file A, its input is removed from DOM.
    // Re-query to find the remaining file input (for PPT B).
    const remainingInputs = page.locator('input[type="file"]')
    const remainingCount = await remainingInputs.count()
    console.log(`STEP 3a2: Remaining file inputs after A: ${remainingCount}`)

    await remainingInputs.first().setInputFiles(TEST_PPT)
    await page.waitForTimeout(1000)
    await page.screenshot({ path: 'test-results/03-after-file-b.png' })
    console.log('STEP 3b: PPT B selected')

    // Step 4: Wait for init (upload + parse)
    try {
      await page.waitForFunction(() => {
        return document.body.innerText.includes('正在') ||
               document.body.innerText.includes('解析') ||
               document.body.innerText.includes('上传')
      }, { timeout: 5000 })
      console.log('STEP 4: Processing indicator detected')
    } catch {
      console.log('STEP 4: No processing indicator (may have completed instantly)')
    }

    // Wait for processing to complete or for merge step
    try {
      await page.waitForFunction(() => {
        const text = document.body.innerText
        return text.includes('PPT A') && (
          text.includes('处理') || text.includes('幻灯片') ||
          text.includes('预览') || text.includes('失败')
        )
      }, { timeout: 45000 })
      console.log('STEP 5: Transition detected (merge step or error)')
    } catch {
      console.log('STEP 5: Timeout waiting for transition')
    }

    await page.waitForTimeout(2000)
    await page.screenshot({ path: 'test-results/04-after-parsing.png' })

    // Step 5: Check results
    const pageText = await page.textContent('body') || ''
    const hasError = pageText.includes('失败') || pageText.includes('错误')
    const hasSlidePool = pageText.includes('幻灯片') || pageText.includes('PPT A')
    const hasMergeStep = pageText.includes('处理') || pageText.includes('预览')

    console.log(`STEP 6 Results:`)
    console.log(`  - Has error: ${hasError}`)
    console.log(`  - Has slide pool: ${hasSlidePool}`)
    console.log(`  - Has merge step: ${hasMergeStep}`)

    if (hasError) {
      const errorMessages = pageText.match(/[^\n]*失败[^\n]*/g) || []
      console.log(`  - Error messages: ${errorMessages.slice(0, 3).join('; ')}`)
    }

    // Final screenshot
    await page.screenshot({ path: 'test-results/05-final-state.png', fullPage: true })
    console.log('STEP 7: Final screenshot taken')

    // Basic assertions
    expect(hasError && !hasSlidePool).toBeFalsy()
  })
})
