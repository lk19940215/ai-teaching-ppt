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
  
  // 上传 100 页 PPT 文件
  console.log('上传 100 页 PPT 文件...');
  const fileInput = await page.$('input[type="file"]');
  const uploadStart = Date.now();
  
  await fileInput.setInputFiles('E:/Code/ai-teaching-ppt/backend/tests/fixtures/large_test.pptx');
  console.log('文件选择完成，等待解析和渲染...');
  
  // 等待 Canvas 渲染完成（最多 60 秒）
  try {
    await page.waitForSelector('[class*="PptCanvasRenderer"] canvas, [class*="ppt-canvas"] canvas', { 
      timeout: 60000,
      state: 'attached'
    });
  } catch (e) {
    console.log('等待 Canvas 渲染超时，尝试等待页面数据显示...');
    await page.waitForSelector('text=共 100 页', { timeout: 10000 });
  }
  
  const renderTime = Date.now() - uploadStart;
  console.log(`渲染时间：${renderTime}ms`);
  
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
  console.log(`渲染时间：${renderTime}ms`);
  console.log(`内存使用：${performanceMetrics.memory ? Math.round(performanceMetrics.memory.usedJSHeapSize / 1024 / 1024) : 'N/A'}MB`);
  
  // 检查是否达标
  console.log('\n=== 性能标准判定 ===');
  const renderOk = renderTime < 10000;
  console.log(`渲染时间 <10 秒：${renderOk ? '✓ 通过' : '✗ 失败'} (${renderTime}ms)`);
  
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
| 渲染时间 | ${renderTime}ms | <10000ms | ${renderOk ? '✓ 通过' : '✗ 失败'} |
| 内存使用 | ${performanceMetrics.memory ? Math.round(performanceMetrics.memory.usedJSHeapSize / 1024 / 1024) : 'N/A'}MB | <50MB | ${performanceMetrics.memory ? (performanceMetrics.memory.usedJSHeapSize < 50 * 1024 * 1024 ? '✓ 通过' : '✗ 失败') : 'N/A'} |

## 详细数据

### 导航性能
- 导航耗时：${navTime}ms
- DOM 加载完成：${performanceMetrics.navigationTiming}ms

### 渲染性能
- 文件上传到渲染完成：${renderTime}ms
- 渲染 100 页，平均每页：${Math.round(renderTime / 100)}ms

### 内存使用
- JS 堆内存：${performanceMetrics.memory ? Math.round(performanceMetrics.memory.usedJSHeapSize / 1024 / 1024) : 'N/A'}MB
- 总 JS 堆：${performanceMetrics.memory ? Math.round(performanceMetrics.memory.totalJSHeapSize / 1024 / 1024) : 'N/A'}MB

## 结论

${renderOk ? '### ✓ 性能测试通过' : '### ✗ 性能测试失败'}

渲染时间 ${renderTime}ms，${renderOk ? '符合' : '不符合'} <10 秒 的标准。
`;

  // 写入报告文件
  const fs = require('fs');
  fs.writeFileSync('E:/Code/ai-teaching-ppt/record/performance-test.md', report);
  console.log('报告已保存到 record/performance-test.md');
})();
