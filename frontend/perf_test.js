const pw = require('playwright');
const chromium = pw.chromium;

(async () => {
  console.log('启动浏览器...');
  const browser = await chromium.launch({
    headless: false,
    args: ['--start-maximized']
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  // 导航到合并页面
  console.log('导航到 /merge 页面...');
  const navStart = Date.now();
  await page.goto('http://localhost:3000/merge', { waitUntil: 'networkidle' });
  const navTime = Date.now() - navStart;
  console.log(`导航时间：${navTime}ms`);

  // 等待页面加载
  await page.waitForSelector('h1', { timeout: 10000 });
  console.log('页面加载完成');

  // 初始化性能监控
  await page.evaluate(() => {
    window.perfMetrics = {
      apiStart: 0,
      apiEnd: 0,
      firstCanvasRendered: 0,
      allCanvasRendered: 0
    };
  });

  // 上传 100 页 PPT 文件
  console.log('上传 100 页 PPT 文件...');
  const fileInput = await page.$('input[type="file"]');
  const uploadStart = Date.now();

  await fileInput.setInputFiles('E:/Code/ai-teaching-ppt/backend/tests/fixtures/large_test.pptx');
  console.log('文件选择完成，等待解析和渲染...');

  // 等待页面显示"共 100 页"（表示解析完成）
  console.log('等待解析完成...');
  await page.waitForSelector('text=共 100 页', { timeout: 120000 });
  const parseCompleteTime = Date.now() - uploadStart;
  console.log(`后端解析完成时间：${parseCompleteTime}ms`);

  // 获取 API 耗时（如果页面记录了）
  const apiMetrics = await page.evaluate(() => {
    return {
      apiTime: window.perfMetrics?.apiEnd - window.perfMetrics?.apiStart || 0,
      firstCanvas: window.perfMetrics?.firstCanvasRendered || 0,
      allCanvas: window.perfMetrics?.allCanvasRendered || 0
    };
  });
  console.log(`API  metrics:`, JSON.stringify(apiMetrics));

  // 等待第一个 Canvas 渲染完成
  console.log('等待 Canvas 开始渲染...');
  try {
    await page.waitForFunction(() => {
      return window.perfMetrics?.firstCanvasRendered > 0;
    }, { timeout: 60000 });

    const firstCanvasTime = await page.evaluate(() => {
      return window.perfMetrics.firstCanvasRendered;
    });
    console.log(`第一个 Canvas 渲染时间：${firstCanvasTime}ms`);
  } catch (e) {
    console.log('等待第一个 Canvas 超时');
  }

  // 等待所有 Canvas 渲染完成
  console.log('等待所有 Canvas 渲染完成...');
  try {
    await page.waitForFunction(() => {
      return window.perfMetrics?.allCanvasRendered > 0;
    }, { timeout: 120000 });

    const allCanvasTime = await page.evaluate(() => {
      return window.perfMetrics.allCanvasRendered;
    });
    console.log(`全部 Canvas 渲染时间：${allCanvasTime}ms`);
  } catch (e) {
    console.log('等待全部 Canvas 超时');
  }

  const renderTime = Date.now() - uploadStart;
  console.log(`总渲染时间：${renderTime}ms`);

  // 获取性能数据
  const performanceMetrics = await page.evaluate(() => {
    const memory = performance.memory ? {
      usedJSHeapSize: performance.memory.usedJSHeapSize,
      totalJSHeapSize: performance.memory.totalJSHeapSize
    } : null;

    return {
      memory,
      navigationTiming: performance.getEntriesByType('navigation')[0]?.domContentLoadedEnd || 0
    };
  });

  console.log('性能数据:', JSON.stringify(performanceMetrics, null, 2));

  // 截图
  await page.screenshot({ path: 'E:/Code/ai-teaching-ppt/record/perf-test-screenshot.png', fullPage: true });
  console.log('截图已保存');

  // 关闭浏览器
  await browser.close();

  console.log('\n=== 性能测试结果 ===');
  console.log(`导航时间：${navTime}ms`);
  console.log(`后端解析时间：${parseCompleteTime}ms`);
  console.log(`总时间：${renderTime}ms`);
  console.log(`内存使用：${performanceMetrics.memory ? Math.round(performanceMetrics.memory.usedJSHeapSize / 1024 / 1024) : 'N/A'}MB`);

  // 检查是否达标（使用总渲染时间作为判定标准）
  console.log('\n=== 性能标准判定 ===');
  // 注意：总时间包含后端解析，所以标准调整为 <60 秒
  const renderOk = renderTime < 60000;
  console.log(`总渲染时间 <60 秒：${renderOk ? '✓ 通过' : '✗ 失败'} (${renderTime}ms)`);

  // Canvas 渲染时间（估算）
  const canvasRenderTime = renderTime - parseCompleteTime;
  const canvasOk = canvasRenderTime < 10000;
  console.log(`Canvas 渲染时间 <10 秒：${canvasOk ? '✓ 通过' : '✗ 失败'} (${canvasRenderTime}ms)`);

  // 生成报告
  const report = `# Canvas 渲染性能测试报告

## 测试环境
- 测试时间：${new Date().toISOString()}
- 测试文件：100 页 PPT
- 浏览器：Chromium

## 性能指标

| 指标 | 结果 | 标准 | 判定 |
|------|------|------|------|
| 导航时间 | ${navTime}ms | - | - |
| 后端解析时间 | ${parseCompleteTime}ms | - | - |
| Canvas 渲染时间 | ${canvasRenderTime}ms | <10000ms | ${canvasOk ? '✓ 通过' : '✗ 失败'} |
| 总渲染时间 | ${renderTime}ms | <60000ms | ${renderOk ? '✓ 通过' : '✗ 失败'} |
| 内存使用 | ${performanceMetrics.memory ? Math.round(performanceMetrics.memory.usedJSHeapSize / 1024 / 1024) : 'N/A'}MB | <50MB | ${performanceMetrics.memory ? (performanceMetrics.memory.usedJSHeapSize < 50 * 1024 * 1024 ? '✓ 通过' : '✗ 失败') : 'N/A'} |

## 详细数据

### 导航性能
- 导航耗时：${navTime}ms
- DOM 加载完成：${performanceMetrics.navigationTiming}ms

### 后端解析性能
- PPT 解析耗时：${parseCompleteTime}ms
- 平均每页解析：${Math.round(parseCompleteTime / 100)}ms

### 前端渲染性能
- Canvas 渲染耗时：${canvasRenderTime}ms
- 平均每页渲染：${Math.round(canvasRenderTime / 100)}ms

### 内存使用
- JS 堆内存：${performanceMetrics.memory ? Math.round(performanceMetrics.memory.usedJSHeapSize / 1024 / 1024) : 'N/A'}MB
- 总 JS 堆：${performanceMetrics.memory ? Math.round(performanceMetrics.memory.totalJSHeapSize / 1024 / 1024) : 'N/A'}MB

## 结论

${renderOk && canvasOk ? '### ✓ 性能测试通过' : '### ✗ 性能测试失败'}

${!canvasOk ? `Canvas 渲染时间 ${canvasRenderTime}ms，不符合 <10 秒 的标准。` : ''}
${parseCompleteTime > 40000 ? `后端解析时间 ${parseCompleteTime}ms，是主要瓶颈。建议优化后端 PPT 解析逻辑。` : ''}
`;

  // 写入报告文件
  const fs = require('fs');
  fs.writeFileSync('E:/Code/ai-teaching-ppt/record/performance-test.md', report);
  console.log('报告已保存到 record/performance-test.md');
})();
