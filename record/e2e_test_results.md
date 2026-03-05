# E2E 测试结果 - feat-047 场景 A

**日期**: 2026-03-05
**工具**: Playwright MCP
**凭证**: playwright-auth.json (storageState)
**会话**: Session 2

## 结果摘要

| 场景 | 结果 | 耗时 | 关键发现 |
|------|------|------|----------|
| A: 数学 PPT 生成 | ⚠️ 受阻 | 180s+ | 凭证注入失效 + SSE 连接超时 |

## 详细记录

### 场景 A: 文字输入 → 生成数学 PPT

**步骤执行**:
1. ✅ browser_navigate → http://localhost:3000/upload - 页面正常加载
2. ✅ browser_snapshot - 找到文本输入框和配置组件
3. ✅ browser_fill - 填写数学测试内容（258 字）
4. ✅ browser_select - 选择年级=小学五年级、学科=数学、风格=活泼趣味
5. ✅ browser_click - 点击"生成教学 PPT"按钮
6. ❌ 等待循环 - 进度卡在 20% "正在连接生成服务..."，180 秒无变化

**问题 1: 凭证注入失效**
- playwright-auth.json 包含有效 llm_config
- .mcp.json 配置了 --storage-state=.claude-coder\playwright-auth.json
- 但浏览器 localStorage 未自动注入凭证
- 页面显示"API Key 未配置"错误
- **临时解决**: 使用 browser_run_code 手动注入 localStorage

**问题 2: 后端服务崩溃**
- 测试过程中后端服务无响应（curl 超时）
- PID 1448 的 uvicorn 进程自动退出
- **临时解决**: 重启后端服务

**问题 3: SSE 连接超时**
- 前端成功发送请求到 /api/v1/ppt/generate-stream
- 后端接收请求但 30 秒内无 SSE 响应
- 进度一直卡在 20% "正在连接生成服务..."
- 可能原因：
  - LLM API 调用超时
  - SSE 流式响应未正确实现
  - 后端异步任务处理问题

**截图/快照**:
- 页面 URL: http://localhost:3000/upload
- 最后状态：进度 20%，按钮显示"AI 正在备课中..." [disabled]

**控制台消息**: 无错误（仅 React DevTools 提示信息）

**网络请求**:
- GET /api/v1/config/providers/default → 200 OK
- GET /api/v1/ppt/generate-stream?... → 已发送，无响应

## 结论

**结果**: 受阻（非测试用例失败，是基础设施问题）

**根因分析**:
1. feat-046 的 Playwright storageState 注入未正确工作
2. 后端服务稳定性问题（进程意外退出）
3. SSE 流式生成 API 响应超时

**建议修复**:
1. 检查 Playwright MCP 是否正确配置 storageState 路径
2. 检查后端日志定位 uvicorn 崩溃原因
3. 测试 LLM API 直连确认凭证有效
4. 验证 SSE 端点 /api/v1/ppt/generate-stream 的实现

**下一步**:
- 优先修复 feat-046 的凭证注入问题
- 排查后端服务稳定性
- 单独测试 LLM API 调用

---

# E2E 测试结果 - feat-048 图片上传 OCR 流程测试

**日期**: 2026-03-05
**工具**: Playwright MCP + 替代测试方案
**会话**: Session 3

## 结果摘要

| 测试场景 | 结果 | 说明 |
|---------|------|------|
| 图片上传 API | ✅ 通过 | 图片成功上传到后端 |
| OCR 识别 API | ❌ 失败 | PaddleOCR 未安装 |
| 文字输入生成流程 | ✅ 通过 | 完整流程正常，生成 16 页 PPT |
| PPT 预览功能 | ✅ 通过 | 缩略图轮播、翻页正常 |
| 下载功能 | ✅ 通过 | 下载按钮触发正常 |

## 详细记录

### 场景 1: 图片上传 API 测试

**步骤**:
1. 创建测试图片 record/test_image.png（含数学教学内容）
2. 使用 curl POST 上传图片到 /api/v1/upload/image
3. 验证返回结果

**结果**:
```json
{"message":"图片上传成功","saved_files":[{"filename":"test_image.png","saved_path":"images/4de6358cd0574ab2ae8ff7b18a08d3b2.png","size":54273}]}
```

**结论**: ✅ 通过

### 场景 2: OCR 识别 API 测试

**步骤**:
1. 使用上传返回的文件路径调用 /api/v1/process/ocr
2. 验证 OCR 识别结果

**结果**:
```json
{"detail":"OCR 识别失败：OCR 引擎初始化失败：No module named 'paddle'"}
```

**结论**: ❌ 失败 - 环境问题

**根因分析**: 后端环境未安装 PaddlePaddle/PaddleOCR

**解决方案**:
```bash
pip install paddlepaddle paddleocr
```

详见：record/ocr_env_issue.md

### 场景 3: 文字输入完整生成流程测试（Playwright MCP）

**步骤**:
1. 使用 Playwright MCP 访问 http://localhost:3000/upload
2. 填写数学测试内容（三角形面积，258 字）
3. 点击"生成教学 PPT"按钮
4. 等待 SSE 推送进度
5. 验证 PPT 预览展示

**结果**:
- 生成时间：约 90 秒
- PPT 页数：16 页
- 页面类型：封面、知识点讲解、例题精讲、变式练习、课堂小结等

**结论**: ✅ 通过

### 场景 4: PPT 预览与下载测试

**步骤**:
1. 验证缩略图轮播区域显示
2. 点击"下载 PPT"按钮
3. 验证下载触发

**结果**:
- 16 个缩略图正常显示
- 翻页功能正常
- 下载按钮点击正常

**结论**: ✅ 通过

## 发现的问题

### 问题 1: OCR 引擎未安装

- **严重程度**: 高
- **影响范围**: 图片上传功能完全不可用
- **根因**: 后端环境缺少 PaddlePaddle 和 PaddleOCR 依赖
- **建议修复**: `pip install paddlepaddle paddleocr`

### 问题 2: Playwright MCP 工具参数格式问题

- **严重程度**: 中
- **影响范围**: 自动化测试无法直接使用 browser_file_upload、browser_select_option 等工具
- **现象**: 参数验证失败（期望数组但收到字符串）
- ** workaround**: 使用 browser_type、browser_click 等替代工具

## 测试结论

1. **核心生成流程**: ✅ 正常工作
2. **文字输入模式**: ✅ 正常工作
3. **PPT 预览和下载**: ✅ 正常工作
4. **图片上传功能**: ❌ 因 OCR 环境缺失暂不可用

**建议**: 安装 PaddleOCR 后重新测试图片上传完整链路。
