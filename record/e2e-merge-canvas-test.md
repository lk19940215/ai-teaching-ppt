# E2E 合并功能测试报告 (feat-093)

## 测试日期
2026-03-08

## 测试环境
- 后端：FastAPI on port 8003
- 前端：Next.js 15 on port 3000
- 浏览器：Playwright MCP (persistent mode)

## 测试项目

### 1. 文件上传 + Canvas 渲染
- **操作**: 上传 ppt_a.pptx 和 ppt_b.pptx
- **预期**: Canvas 显示分页预览
- **结果**: ✅ 通过
  - PPT A 显示 5 页预览（P2-P6 带缓存标记）
  - PPT B 显示 5 页预览
  - Canvas 渲染正常

### 2. 页面选择 + 提示语联动
- **操作**: 点击 Canvas 页面
- **预期**: 右侧提示语面板自动定位到对应输入框
- **结果**: ✅ 通过
  - 点击 PPT A 第 2 页 → 右侧显示"PPT A: P2"
  - 提示语输入框自动聚焦

### 3. 智能合并 API
- **操作**: POST /api/v1/ppt/smart-merge-stream
- **预期**: 返回合并后的 PPT 下载链接
- **结果**: ✅ 通过
  ```
  data: {"stage": "uploading_files", "progress": 10, ...}
  data: {"stage": "parsing_ppt", "progress": 25, ...}
  data: {"stage": "generating_strategy", "progress": 50, ...}
  data: {"stage": "merging_ppt", "progress": 75, ...}
  data: {"stage": "complete", "progress": 100, "result": {...}}
  ```

### 4. LLM JSON 解析修复
- **问题**: LLM 返回 markdown 代码块包裹的 JSON，原代码无法解析
- **修复**: 添加 `_extract_json_from_response()` 调用
- **结果**: ✅ 通过
  - 提取 markdown 代码块中的 JSON
  - 修复格式后成功解析

### 5. 错误消息修复
- **问题**: HTTPException 的 str(e) 返回空字符串
- **修复**: 使用 `e.detail` 获取错误详情
- **结果**: ✅ 通过

## 修复内容

### backend/app/api/ppt.py
1. 添加 JSON 提取逻辑（处理 markdown 代码块）
2. 修复错误消息为空的问题
3. 添加详细日志记录
4. 修复 MSO_AUTO_SHAPE_TYPE 导入兼容性问题

## 测试结论

**feat-093 Playwright 端到端测试：文件上传+Canvas 渲染 + 合并** - ✅ 通过

所有核心功能已验证：
- ✅ 文件上传
- ✅ Canvas 渲染
- ✅ 页面选择联动
- ✅ 智能合并 API
- ✅ 下载链接生成

## 备注
- 后端端口从 8000 切换到 8003（8000 端口有僵尸进程无法清理）
- 前端 .env.local 已更新为 `NEXT_PUBLIC_API_URL=http://localhost:8003`
