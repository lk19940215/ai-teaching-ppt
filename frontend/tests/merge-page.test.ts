import { test, expect } from '@playwright/test';

// 测试文件路径（使用绝对路径）
const PPT_A_PATH = 'E:/Code/ai-teaching-ppt/backend/tests/fixtures/ppt_a.pptx';
const PPT_B_PATH = 'E:/Code/ai-teaching-ppt/backend/tests/fixtures/ppt_b.pptx';

test.describe('PPT 智能合并页面 - feat-078', () => {
  test('页面加载和导航', async ({ page }) => {
    await page.goto('http://localhost:3000/merge');

    // 验证页面标题
    await expect(page.getByRole('heading', { name: 'PPT 智能合并' })).toBeVisible();

    // 验证描述文本
    await expect(page.getByText('上传两个 PPT 文件，通过 AI 提示语指导，智能合并生成新的教学课件')).toBeVisible();
  });

  test('上传 PPT A 文件', async ({ page }) => {
    await page.goto('http://localhost:3000/merge');

    // 等待上传区域加载
    await page.waitForSelector('text=PPT A（基础课件）');

    // 上传 PPT A
    const fileInput = page.getByLabel('PPT A（基础课件）').locator('input[type="file"]');
    await fileInput.setInputFiles(PPT_A_PATH);

    // 等待文件名显示
    await page.waitForSelector('text=ppt_a.pptx');

    // 验证文件名显示
    await expect(page.getByText('ppt_a.pptx')).toBeVisible();
  });

  test('上传两个 PPT 文件并验证预览', async ({ page }) => {
    await page.goto('http://localhost:3000/merge');

    // 上传 PPT A
    const fileInputA = page.getByLabel('PPT A（基础课件）').locator('input[type="file"]');
    await fileInputA.setInputFiles(PPT_A_PATH);
    await page.waitForSelector('text=ppt_a.pptx');

    // 上传 PPT B
    const fileInputB = page.getByLabel('PPT B（补充内容）').locator('input[type="file"]');
    await fileInputB.setInputFiles(PPT_B_PATH);
    await page.waitForSelector('text=ppt_b.pptx');

    // 等待解析完成
    await page.waitForTimeout(2000);

    // 验证 PPT A 预览区域显示
    await expect(page.getByText('PPT A 预览')).toBeVisible();

    // 验证 PPT B 预览区域显示
    await expect(page.getByText('PPT B 预览')).toBeVisible();
  });

  test('选择页面并验证提示语面板联动', async ({ page }) => {
    await page.goto('http://localhost:3000/merge');

    // 上传 PPT A
    const fileInputA = page.getByLabel('PPT A（基础课件）').locator('input[type="file"]');
    await fileInputA.setInputFiles(PPT_A_PATH);
    await page.waitForSelector('text=ppt_a.pptx');

    // 等待解析完成
    await page.waitForTimeout(2000);

    // 选择第一个页面（点击缩略图）
    const thumbnails = page.locator('.ppt-canvas-preview .grid button');
    await thumbnails.first().click();

    // 验证已选择页面提示
    await expect(page.getByText('已选择页面：').nth(0)).toBeVisible();
    await expect(page.getByText('PPT A: P1')).toBeVisible();
  });

  test('点击合并按钮验证错误处理', async ({ page }) => {
    await page.goto('http://localhost:3000/merge');

    // 直接点击合并按钮（没有上传文件）
    await page.getByRole('button', { name: '开始智能合并' }).click();

    // 验证错误提示
    await expect(page.locator('.bg-red-50')).toBeVisible();
    await expect(page.getByText('请上传 A/B 两个 PPT 文件')).toBeVisible();
  });

  test('重置功能', async ({ page }) => {
    await page.goto('http://localhost:3000/merge');

    // 上传 PPT A
    const fileInputA = page.getByLabel('PPT A（基础课件）').locator('input[type="file"]');
    await fileInputA.setInputFiles(PPT_A_PATH);
    await page.waitForSelector('text=ppt_a.pptx');

    // 点击重置按钮
    await page.getByRole('button', { name: '重置' }).click();

    // 验证文件已移除
    await expect(page.getByText('PPT A（基础课件）')).toBeVisible();
    await expect(page.getByText('ppt_a.pptx')).toBeHidden();
  });
});
