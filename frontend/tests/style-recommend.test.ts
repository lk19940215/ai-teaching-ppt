import { test, expect } from '@playwright/test';

test.describe('智能风格推荐 - feat-053', () => {
  test('根据年级自动推荐风格', async ({ page }) => {
    await page.goto('http://localhost:3000/upload');

    // 测试 1: 小学一年级 → 活泼趣味 (fun)
    await page.getByLabel('年级').selectOption('1');
    await page.waitForTimeout(500);
    let styleValue = await page.getByLabel('PPT 风格').inputValue();
    console.log('选择一年级后风格:', styleValue);
    expect(styleValue).toBe('fun');

    // 测试 2: 小学五年级 → 简约清晰 (simple)
    await page.getByLabel('年级').selectOption('5');
    await page.waitForTimeout(500);
    styleValue = await page.getByLabel('PPT 风格').inputValue();
    console.log('选择五年级后风格:', styleValue);
    expect(styleValue).toBe('simple');

    // 测试 3: 高中一年级 → 学科主题 (theme)
    await page.getByLabel('年级').selectOption('10');
    await page.waitForTimeout(500);
    styleValue = await page.getByLabel('PPT 风格').inputValue();
    console.log('选择高一年级后风格:', styleValue);
    expect(styleValue).toBe('theme');
  });

  test('用户手动修改后不再自动推荐', async ({ page }) => {
    await page.goto('http://localhost:3000/upload');

    // 先选择小学一年级（应该自动推荐 fun）
    await page.getByLabel('年级').selectOption('1');
    await page.waitForTimeout(500);

    // 手动修改为简约清晰
    await page.getByLabel('PPT 风格').selectOption('simple');
    await page.waitForTimeout(100);

    // 再选择小学三年级，风格应该保持 simple（不自动改变）
    await page.getByLabel('年级').selectOption('3');
    await page.waitForTimeout(500);

    const styleValue = await page.getByLabel('PPT 风格').inputValue();
    console.log('手动修改后选择三年级的风格:', styleValue);
    expect(styleValue).toBe('simple'); // 应该保持用户手动选择的值
  });
});
