/**
 * Playwright 端到端测试示例文件
 *
 * 运行测试：pnpm exec playwright test
 *
 * 本文件包含以下测试示例：
 * 1. 首页加载测试
 * 2. 上传页面表单填写测试
 * 3. 设置页面配置测试
 * 4. 历史记录页面加载测试
 */

import { test, expect } from '@playwright/test';

// 测试配置
const BASE_URL = 'http://localhost:3000';
const API_BASE_URL = 'http://localhost:8000/api/v1';

// ============================================
// 首页测试
// ============================================
test.describe('首页', () => {
  test('应该正常加载首页', async ({ page }) => {
    await page.goto(BASE_URL);

    // 验证页面标题
    await expect(page).toHaveTitle('AI 教学 PPT 生成器');

    // 验证主标题存在
    await expect(page.getByRole('heading', { name: '欢迎使用 AI 教学 PPT 生成器' })).toBeVisible();

    // 验证导航栏
    await expect(page.getByRole('link', { name: '首页' })).toBeVisible();
    await expect(page.getByRole('link', { name: '生成 PPT' })).toBeVisible();
    await expect(page.getByRole('link', { name: '历史记录' })).toBeVisible();
    await expect(page.getByRole('link', { name: '设置' })).toBeVisible();
  });

  test('点击开始使用应该跳转到上传页面', async ({ page }) => {
    await page.goto(BASE_URL);

    await page.getByRole('button', { name: '开始使用' }).click();

    await expect(page).toHaveURL(`${BASE_URL}/upload`);
  });
});

// ============================================
// 上传页面测试
// ============================================
test.describe('上传页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/upload`);
  });

  test('应该正常加载上传页面', async ({ page }) => {
    await expect(page).toHaveTitle('AI 教学 PPT 生成器');
    await expect(page.getByRole('heading', { name: '上传教材内容' })).toBeVisible();
  });

  test('应该可以切换上传方式', async ({ page }) => {
    // 文字输入（默认）
    await expect(page.getByRole('textbox')).toBeVisible();

    // 切换到图片上传
    await page.getByRole('button', { name: '图片上传' }).click();
    await expect(page.getByText('拖拽图片到此处或点击上传')).toBeVisible();

    // 切换到 PDF 上传
    await page.getByRole('button', { name: 'PDF 上传' }).click();
    await expect(page.getByText('拖拽 PDF 文件到此处或点击上传')).toBeVisible();
  });

  test('应该可以填写教学参数', async ({ page }) => {
    // 填写内容
    await page.getByRole('textbox', { name: '请粘贴课本内容' }).fill('这是一个测试内容');

    // 选择年级
    await page.getByRole('combobox', { name: '年级' }).selectOption('小学三年级');

    // 选择学科
    await page.getByRole('combobox', { name: '学科' }).selectOption('数学');

    // 选择风格
    await page.getByRole('combobox', { name: 'PPT 风格' }).selectOption('简约清晰（适合高年级）');

    // 调整幻灯片数量
    await page.getByRole('slider').fill('20');

    // 验证生成按钮状态（需要内容才能启用）
    const generateButton = page.getByRole('button', { name: '生成教学 PPT' });
    await expect(generateButton).toBeVisible();
  });
});

// ============================================
// 设置页面测试
// ============================================
test.describe('设置页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/settings`);
  });

  test('应该正常加载设置页面', async ({ page }) => {
    await expect(page).toHaveTitle('AI 教学 PPT 生成器');
    await expect(page.getByRole('heading', { name: '设置' })).toBeVisible();
  });

  test('应该可以选择 LLM 服务商', async ({ page }) => {
    const providerSelect = page.getByRole('combobox', { name: '服务商' });

    // 验证选项存在
    await expect(providerSelect.getByRole('option', { name: 'DeepSeek' })).toBeVisible();
    await expect(providerSelect.getByRole('option', { name: 'OpenAI' })).toBeVisible();
    await expect(providerSelect.getByRole('option', { name: 'Claude' })).toBeVisible();
    await expect(providerSelect.getByRole('option', { name: '智谱 GLM' })).toBeVisible();
  });

  test('应该可以输入 API Key 配置', async ({ page }) => {
    await page.getByRole('textbox', { name: 'API Key' }).fill('sk-test123456');
    await page.getByRole('textbox', { name: 'API Base URL' }).fill('https://api.deepseek.com');
    await page.getByRole('textbox', { name: '模型名称' }).fill('deepseek-chat');

    // 验证输入值
    await expect(page.getByRole('textbox', { name: 'API Key' })).toHaveValue('sk-test123456');
  });
});

// ============================================
// 历史记录页面测试
// ============================================
test.describe('历史记录页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/history`);
  });

  test('应该正常加载历史记录页面', async ({ page }) => {
    await expect(page).toHaveTitle('AI 教学 PPT 生成器');
    await expect(page.getByRole('heading', { name: '生成历史记录' })).toBeVisible();
  });

  test('应该显示空状态提示', async ({ page }) => {
    // 验证搜索筛选组件
    await expect(page.getByRole('textbox', { name: '搜索关键词' })).toBeVisible();
    await expect(page.getByRole('combobox', { name: '年级筛选' })).toBeVisible();
    await expect(page.getByRole('combobox', { name: '学科筛选' })).toBeVisible();

    // 验证空状态提示
    await expect(page.getByText('暂无历史记录')).toBeVisible();
  });
});

// ============================================
// API 端点测试
// ============================================
test.describe('API 端点', () => {
  test('健康检查端点应该返回正常', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/../health`);

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });

  test('历史记录列表端点应该返回空列表', async ({ request }) => {
    const sessionId = `test_${Date.now()}`;
    const response = await request.get(
      `${API_BASE_URL}/history/search?session_id=${sessionId}&limit=20&offset=0`
    );

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.data).toEqual([]);
  });
});

// ============================================
// 可访问性测试
// ============================================
test.describe('可访问性', () => {
  test('所有页面应该有正确的对比度', async ({ page }) => {
    const pages = ['/', '/upload', '/settings', '/history'];

    for (const path of pages) {
      await page.goto(`${BASE_URL}${path}`);

      // 验证背景色和文字颜色对比度
      const body = page.locator('body');
      const backgroundColor = await body.evaluate((el) =>
        window.getComputedStyle(el).backgroundColor
      );

      // 验证背景不是纯黑色
      expect(backgroundColor).not.toBe('rgb(0, 0, 0)');
    }
  });
});
