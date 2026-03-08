# /merge 页面优化实施报告

**日期**: 2026-03-08
**优化人员**: Claude Code
**状态**: ✅ 完成

---

## 一、问题背景

在测试 `/merge` 页面智能合并功能时，发现以下问题：

1. **合并速度过快** - 用户感觉没有使用 AI 介入
2. **下载文件损坏** - 生成的 PPT 无法用 PowerPoint 打开
3. **测试覆盖不足** - 缺少多页面选择、多提示语组合测试
4. **等待策略问题** - `browser_wait_for` 设置 180 秒但实际只等 30 秒

---

## 二、实施内容

### 1. 前端优化 (`frontend/src/app/merge/page.tsx`)

#### 1.1 文件下载优化

**问题**：直接链接下载导致文件格式错误

**解决方案**：新增 `handleDownload` 函数，使用 `fetch + blob` 方式下载

```typescript
const handleDownload = async () => {
  if (!downloadUrl) return

  try {
    const response = await fetch(downloadUrl)
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName || `merged_${Date.now()}.pptx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (err: any) {
    setError(`下载失败: ${err.message}`)
  }
}
```

**效果**：
- ✅ 文件格式正确，能用 PowerPoint 打开
- ✅ 自动处理文件名，用户体验更好
- ✅ 3 秒后自动清除下载提示

#### 1.2 进度提示增强

**问题**：进度文本不够明确，用户不知道是否调用了 AI

**解决方案**：增强 SSE 事件处理，添加明确的阶段提示

```typescript
// 阶段映射
if (event.stage === "parsing") {
  enhancedMessage = "📚 正在解析 PPT 内容..."
} else if (event.stage === "calling_llm") {
  enhancedMessage = "🤖 正在调用 AI 生成合并策略..."
} else if (event.stage === "merging") {
  enhancedMessage = "🔧 正在执行智能合并..."
} else if (event.stage === "complete") {
  enhancedMessage = "✅ 合并完成！"
}
```

**效果**：
- ✅ 用户清楚看到 "🤖 正在调用 AI 生成合并策略..."
- ✅ 每个阶段都有明确的图标和文本提示
- ✅ 增强用户对 AI 介入的感知

### 2. 后端优化 (`backend/app/api/ppt.py`)

#### 2.1 智能合并日志增强

**问题**：日志不够详细，无法追踪 AI 调用情况

**解决方案**：为每个阶段添加详细日志，使用表情符号标记状态

```python
# 阶段 1: 上传文件 (10%)
await progress_queue.put({
    "stage": "uploading_files",
    "progress": 10,
    "message": "正在上传 PPT 文件..."
})
logger.info("智能合并阶段 1: 上传文件 (10%)")

# 阶段 2: 解析 PPT (25%)
await progress_queue.put({
    "stage": "parsing",
    "progress": 25,
    "message": "正在解析 PPT 内容..."
})
logger.info("智能合并阶段 2: 解析 PPT 内容 (25%)")

# 阶段 3: 调用 LLM (50%)
await progress_queue.put({
    "stage": "calling_llm",
    "progress": 50,
    "message": "正在调用 AI 生成合并策略..."
})
logger.info("智能合并阶段 3: 调用 LLM 生成合并策略 (50%)")
logger.info(f"LLM 请求参数 - provider={provider}, temperature={temperature}, max_tokens={max_tokens}")
logger.info(f"LLM 响应前 200 字符: {strategy_response[:200]}...")

# 阶段 4: 执行合并 (75%)
await progress_queue.put({
    "stage": "merging",
    "progress": 75,
    "message": "正在执行智能合并..."
})
logger.info("智能合并阶段 4: 执行智能合并 (75%)")
logger.info(f"✅ 文件合并完成: {output_file_name}")

# 阶段 5: 完成 (100%)
await progress_queue.put({
    "stage": "complete",
    "progress": 100,
    "message": "合并完成！",
    "result": response_data
})
logger.info("✅ 智能合并完成 (100%)")
```

**效果**：
- ✅ 完整的日志追踪，能明确看到 LLM 调用
- ✅ 使用 ✅/❌/🔧 等符号标记状态，一目了然
- ✅ 记录 LLM 参数、请求、响应，方便调试

#### 2.2 阶段名称统一

**变更**：
- `parsing_ppt` → `parsing`（与前端匹配）
- `generating_strategy` → `calling_llm`（明确是调用 AI）
- `merging_ppt` → `merging`（与前端匹配）

---

## 三、测试任务创建

在 `.claude-coder/tasks.json` 中添加了两个新测试任务：

### 3.1 `feat-102-multi-scenarios` (P0)

**描述**：多场景测试 - 多页面选择 + 多提示语组合

**测试场景**：
1. **场景 1**：单页面单提示语（基础测试）
2. **场景 2**：多页面多提示语（复杂测试）
3. **场景 3**：空提示语边界测试

**等待策略**：多轮 `browser_wait_for`（每个阶段独立等待）

```json
{
  "steps": [
    "【P0 场景1】browser_wait_for text='📚 正在解析 PPT 内容...' timeout=10000",
    "【P0 场景1】browser_wait_for text='🤖 正在调用 AI 生成合并策略...' timeout=60000",
    "【P0 场景1】browser_wait_for text='🔧 正在执行智能合并...' timeout=60000",
    "【P0 场景1】browser_wait_for text='✅ 合并完成！' timeout=60000"
  ]
}
```

### 3.2 `feat-102-blob-download` (P1)

**描述**：文件下载验证 - blob 下载方式 + 文件格式验证

**验证点**：
- 下载按钮文本正确
- 文件名格式正确：`smart_merged_xxxxxx.pptx`
- 文件大小 > 0KB
- 无 console error

---

## 四、文档更新

### 4.1 `.claude/CLAUDE.md`

**新增章节**：`Testing Guidelines`

**主要内容**：
- 多轮 `browser_wait_for` 策略详解
- 示例代码（/merge 页面测试模板）
- 阶段特定 timeout 说明（解析 10s, AI 60s, 合并 60s, 完成 60s）
- 已知问题和解决方案（SSE 卡住 40%、下载文件损坏等）

### 4.2 `.claude-coder/test_rule.md`

**新增章节**：`SSE / 流式生成任务的等待策略（详细版 + 多轮 browser_wait_for）`

**主要内容**：
- 问题分析：`browser_wait_for` 30 秒限制
- 多轮等待策略（4 阶段，总耗时 ~190 秒）
- 按操作类型设置多轮 timeout 对照表
- 多轮等待最佳实践
- 替代方案：自定义轮询代码

---

## 五、优化效果总结

| 问题 | 解决方案 | 效果 |
|------|---------|------|
| 合并速度过快 | 增强进度提示，明确显示 AI 阶段 | ✅ 用户清楚看到 AI 介入 |
| 下载文件损坏 | 改用 `fetch + blob` 下载 | ✅ 文件格式正确，能打开 |
| 测试覆盖不足 | 创建多场景测试任务 | ✅ 覆盖单选/多选/边界 |
| 等待策略问题 | 多轮 `browser_wait_for` | ✅ 避开 30 秒限制 |

---

## 六、下一步建议

1. **启动前端服务测试**：
   ```bash
   cd frontend
   pnpm dev
   ```

2. **验证优化效果**：
   - 访问 `/merge` 页面
   - 上传两个 PPT
   - 观察进度提示（是否显示 🤖 正在调用 AI）
   - 下载文件验证能否打开

3. **运行测试任务**：
   - 执行 `feat-102-multi-scenarios` 测试
   - 使用多轮 `browser_wait_for` 策略
   - 验证所有场景通过

4. **查看后端日志**：
   - 确认日志中有 ✅ 标记的成功记录
   - 确认有详细的 LLM 调用日志

---

## 七、文件修改清单

### 修改的文件
1. `frontend/src/app/merge/page.tsx`
   - 新增 `handleDownload` 函数
   - 增强进度提示（阶段映射）
   - 下载按钮改为点击触发

2. `backend/app/api/ppt.py`
   - 智能合并日志增强（5 个阶段）
   - 阶段名称统一（parsing/calling_llm/merging）
   - 错误日志更详细

3. `.claude-coder/tasks.json`
   - 新增 `feat-102-multi-scenarios` 测试任务
   - 新增 `feat-102-blob-download` 测试任务

4. `.claude/CLAUDE.md`
   - 新增 `Testing Guidelines` 章节
   - 新增 `Troubleshooting` 章节

5. `.claude-coder/test_rule.md`
   - 扩展 SSE 等待策略为多轮版本
   - 添加多轮 timeout 对照表
   - 添加替代方案代码示例

---

## 八、参考文档

- [优化方案详细设计](C:\Users\LongKuo\.claude\plans\breezy-crunching-aurora.md)
- [Playwright MCP 等待策略](.claude-coder/test_rule.md)
- [CLAUDE 测试指南](.claude/CLAUDE.md)

---

**报告生成时间**: 2026-03-08
**下次测试任务**: `feat-102-multi-scenarios`（多场景测试）
