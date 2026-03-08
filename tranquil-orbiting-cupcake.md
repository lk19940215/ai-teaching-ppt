# /merge 页面优化计划

## 用户问题总结

在当前 `/merge` 页面测试中发现了以下问题：

### 1. **问题：PPT 解析失败 - XML 命名空间错误**

**现象**：
- `/api/v1/ppt/parse` 解析某些 PPT 时返回错误：`"PPT 解析失败：xmlns:ns2: '%s' is not a valid URI, line 2, column 86"`
- 示例文件：`三角形的面积_0dc28a00.pptx`
- 可解析文件：`test_ppt_b.pptx`

**根因分析**：
- 错误发生在 `backend/app/api/ppt.py` 的 `parse_ppt()` 函数中（第 829 行）
- 使用 `python-pptx` 库的 `Presentation()` 加载文件时失败
- 错误提示表明 OOXML 文件中有无效的 XML 命名空间声明（xmlns:ns2 URI 格式错误）
- 可能原因：某些 PPT 编辑工具（如 WPS、旧版 PowerPoint）生成了非标准的 OOXML 格式

**影响范围**：
- 直接影响 `/merge` 页面上传功能，导致部分 PPT 无法使用
- 也影响 `/upload` 页面的预览功能

---

### 2. **问题：Canvas 渲染模式不直观**

**现象**：
- 当前使用 `PptCanvasPreview` 组件，显示所有页面的缩略图列表（3 列网格布局）
- 用户反馈：无法看到完整页面内容，预览效果不直观

**当前实现**：
- 文件：`frontend/src/components/ppt-canvas-preview.tsx`（第 591 行）
- 渲染方式：`<div className="grid grid-cols-2 md:grid-cols-3 gap-3">`（缩略图网格）
- 每页使用 `PptCanvasRenderer` 渲染为小缩略图（宽 300 像素）

**用户需求**：
- 只需要渲染**一页**完整内容
- 支持**左右滑动**切换页面（类似 PowerPoint 预览）
- 提供更好的页面内容查看体验

---

### 3. **问题：UI 反馈不足**

**现象**：
- 当前渲染模式下，页面内容被压缩为缩略图，文字可能模糊不清
- 用户难以判断选择的页面是否正确

**影响**：
- 降低用户体验
- 增加操作错误概率

---

### 4. **问题：智能合并是否真的调用 AI？**

**用户疑虑**：
- `smart-merge-stream` 真的调用了 AI 模型来生成新 PPT 吗？
- 还是只是简单的拼接？

**验证结果**：
- **答案：是的，确实调用了 AI 模型**

**证据**：
- 文件：`backend/app/api/ppt.py`（第 1285-1500 行）
- `smart_merge_ppt_stream()` 函数实现包含完整的 AI 调用流程

**完整流程**：
```
1. 上传阶段 (10%)
   └─ 接收 PPT A/B 文件

2. 解析阶段 (25%)
   └─ 使用 python-pptx 提取每页标题和内容摘要
   └─ 提取页面级提示语

3. AI 策略生成阶段 (50%)  ← 核心 AI 调用
   └─ 调用 get_llm_service()（第 1463 行）
   └─ 构造 system_prompt（第 1420-1441 行）
   └─ 构造 user_prompt（第 1443-1459 行）
   └─ llm_service.chat([system_prompt, user_prompt])（第 1473-1476 行）
   └─ LLM 返回 JSON 格式的合并策略

4. 合并执行阶段 (75%)
   └─ 根据 AI 生成的策略调用 python-pptx 执行实际合并
   └─ 调用 services.ppt_generator.smart_merge_ppts()

5. 完成阶段 (100%)
   └─ 保存文件，返回下载链接
```

**AI 生成的内容**：
- `slides_to_merge`: 要合并的页面对象列表（包含 `from_a`, `from_b`, `action` 等）
- `slides_to_skip_a/b`: 从 A/B 中跳过的页码
- `global_adjustments`: 全局调整说明

**结论**：该功能确实调用了 AI（DeepSeek、OpenAI 等），AI 负责理解用户提示语并生成**合并策略**，然后后端根据策略执行实际的 PPT 合并操作。

---

## 解决方案

### 问题 1：XML 命名空间错误

**方案**：增强错误处理，提供降级渲染模式

**实施步骤**：
1. 在 `parse_ppt()` 中捕获 XML 解析异常
2. 记录详细错误信息（文件名、错误类型）
3. 尝试使用 `extract_enhanced=False` 降级模式重试
4. 如果仍失败，返回明确的错误提示

**代码位置**：
- `backend/app/api/ppt.py`（第 820-830 行）

---

### 问题 2：单页预览 + 滑动切换

**方案**：重构预览组件为单页模式

**设计思路**：
1. 创建新的 `PptCanvasSinglePagePreview` 组件
2. 核心功能：
   - 只渲染**当前选中**的一页（完整尺寸）
   - 左右箭头按钮切换页面
   - 底部显示页码指示器（圆点）
   - 缩略图面板作为页面选择器（可选）

**组件结构**：
```tsx
<div className="flex flex-col gap-4">
  {/* 主预览区：当前页完整渲染 */}
  <div className="bg-white rounded-lg overflow-hidden border border-gray-200">
    <PptCanvasRenderer
      pageData={currentPage}
      width={800}  // 完整宽度
      height={450} // 完整高度
    />
  </div>

  {/* 页码控制 */}
  <div className="flex items-center justify-between">
    <button onClick={prevPage}>←</button>
    <span>第 {currentPageIndex} 页 / {totalPages} 页</span>
    <button onClick={nextPage}>→</button>
  </div>

  {/* （可选）缩略图选择器 */}
  <div className="grid grid-cols-5 gap-2 overflow-x-auto">
    {allPages.map((page, index) => (
      <div
        key={index}
        onClick={() => setCurrentPage(index)}
        className={index === currentPageIndex ? 'border-2 border-indigo-500' : ''}
      >
        <PptCanvasRenderer pageData={page} width={100} height={56} />
      </div>
    ))}
  </div>
</div>
```

**实现位置**：
- 新文件：`frontend/src/components/ppt-canvas-single-page-preview.tsx`
- 修改：`frontend/src/app/merge/page.tsx`（替换 `PptCanvasPreview` 为新组件）

**工作量评估**：
- 新组件：~150 行代码
- 样式调整：~50 行 Tailwind CSS
- 测试：1-2 小时

---

### 问题 3：优化用户提示语编辑体验

**方案**：增强当前页与提示语的联动

**改进点**：
1. 当前预览的页面对应的提示语输入框**自动高亮**
2. 滚动到当前预览页面时，对应的提示语输入框自动聚焦
3. 页面切换时，右侧提示语面板**自动滚动**到对应位置

**实现**：
- 使用 `scrollIntoView()` 方法
- 添加过渡动画
- 高亮样式：`.focus:ring-2 ring-indigo-300`

---

## 实施优先级

| 优先级 | 任务 | 预计工时 | 影响范围 |
|--------|------|----------|----------|
| P0 | XML 解析错误降级处理 | 1 小时 | 所有 PPT 上传 |
| P1 | 单页预览组件开发 | 4 小时 | /merge 页面 |
| P2 | 提示语输入框自动高亮 | 1 小时 | /merge 页面 |
| P3 | 滑动手势支持（移动端） | 2 小时 | 移动端体验 |

**总预估**：8 小时

---

## 验证计划

### 1. XML 解析降级验证
```bash
# 上传有问题的文件
curl -X POST -F "file=@三角形的面积_0dc28a00.pptx" \
  http://localhost:8000/api/v1/ppt/parse

# 验证返回错误信息（而非 500）
# 验证日志中有详细错误记录
```

### 2. 单页预览验证
- [ ] 上传 PPT A，验证首页完整渲染
- [ ] 点击下一页按钮，验证页面切换
- [ ] 验证左右箭头键可切换页面
- [ ] 验证页码指示器正确更新
- [ ] 验证缩略图选择器可用（可选）

### 3. AI 调用验证
- [ ] 查看后端日志，确认 `logger.info("LLM 服务初始化完成，开始调用 chat API...")`
- [ ] 查看 LLM 请求和响应内容
- [ ] 验证合并策略确实来自 AI（非硬编码）

---

## 关键文件清单

| 文件路径 | 说明 | 修改类型 |
|---------|------|----------|
| `backend/app/api/ppt.py` | PPT 解析和合并逻辑 | 修改 |
| `frontend/src/app/merge/page.tsx` | /merge 页面主组件 | 修改 |
| `frontend/src/components/ppt-canvas-preview.tsx` | 缩略图预览组件 | 保持不变 |
| `frontend/src/components/ppt-canvas-renderer.tsx` | Canvas 渲染器 | 保持不变 |
| `frontend/src/components/ppt-canvas-single-page-preview.tsx` | **新建：单页预览组件** | 新建 |

---

## 备注

1. **AI 调用确认**：经过代码审查确认，`/api/v1/ppt/smart-merge-stream` 确实调用了 AI 模型生成合并策略，流程完整且合理。

2. **Canvas 使用确认**：前端确实使用 Canvas 渲染 PPT 内容（`PptCanvasRenderer` 组件），支持文本、图片、表格、形状等元素。

3. **建议的后续优化**：
   - 添加触摸滑动手势支持（Hammer.js 或原生 touch events）
   - 添加键盘快捷键（←/→ 箭头键）
   - 添加全屏预览模式
