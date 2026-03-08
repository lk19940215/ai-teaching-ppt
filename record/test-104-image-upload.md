# feat-104 P1 图片上传测试报告

**测试日期**: 2026-03-08
**测试会话**: Session 3
**测试状态**: ❌ 部分通过（OCR 识别成功，PPT 生成卡住）

---

## 测试概述

测试图片上传 → OCR 识别 → 内容显示 → 生成 PPT 的完整流程。

---

## 测试结果

### ✅ 通过项

1. **图片上传功能**
   - 前端图片选择器正常工作
   - 图片文件成功上传到后端 `/api/v1/upload/image`
   - 后端返回保存路径：`images/{uuid}.png`
   - 前端显示"已选择 1 张图片：test_image.png"

2. **OCR 识别功能**
   - 后端 `/api/v1/process/ocr` API 工作正常
   - 使用 PaddleOCR 成功识别图片中的中文文本
   - 识别结果：
     ```
     三角形的面积公式
     三角形的面积等于底乘以高除以二。
     公式：S=a×h÷2
     其中：
     - S 表示面积
     - a 表示底边长度
     - h 表示底边上的高
     示例：
     一个底为 6 厘米、高为 4 厘米的三角形
     面积 = 6 × 4 ÷ 2 = 12 平方厘米
     注意：底和高必须是对应的！
     ```
   - 文本清洗和关键词提取功能正常

3. **前端 UI 响应**
   - 图片上传后生成按钮自动启用
   - 点击生成后显示进度条和状态信息
   - 进度显示"正在上传 1 张图片..." (10%) → "正在连接生成服务..." (40%)

### ❌ 失败项

1. **SSE 流式生成卡住**
   - 进度卡在 40% "正在连接生成服务..."
   - 前端 EventSource 连接建立，但未收到后端 SSE 数据
   - 网络请求显示 `GET /api/v1/ppt/generate-stream` 已发送
   - 后端日志未显示明显错误
   - 问题可能原因：
     - 后端 `asyncio.Queue` 初始化后后台任务未及时启动
     - LLM API 调用超时或阻塞
     - SSE StreamingResponse 未正确刷新

---

## 测试步骤复现

1. 导航到 `http://localhost:3000/upload`
2. 点击"图片上传"按钮
3. 选择测试图片 `record/test_image.png`
4. 图片上传成功，显示文件名
5. 点击"生成教学 PPT"按钮
6. 进度条显示 10% → 40%
7. 进度卡在 40% 超过 180 秒

---

## 后端 API 验证

### OCR API（直接调用）
```bash
curl -X POST http://localhost:8000/api/v1/process/ocr \
  -H "Content-Type: application/json" \
  -d '{"file_path": "images/test.png", "language": "ch"}'
```
**结果**: ✅ 成功返回识别文本

### 图片上传 API（直接调用）
```bash
curl -X POST http://localhost:8000/api/v1/upload/image \
  -F "files=@record/test_image.png"
```
**结果**: ✅ 成功返回保存路径

### SSE 生成 API（直接调用）
```bash
curl "http://localhost:8000/api/v1/ppt/generate-stream?text_content=test&grade=5&subject=math&slide_count=10&provider=deepseek&api_key=sk-xxx&style=simple&session_id=test"
```
**结果**: ❌ 请求挂起，无响应

---

## 问题分析

1. **SSE 端点问题**: 后端 `/api/v1/ppt/generate-stream` GET 端点在接收到请求后，创建了 `asyncio.Queue` 和后台任务，但第一个 SSE 事件（10% 进度）似乎没有被发送到队列或被前端接收。

2. **可能的根本原因**:
   - `asyncio.sleep(0)` 让出控制权后，后台任务可能没有立即执行
   - `await progress_queue.put()` 可能阻塞
   - LLM 服务调用可能在获取服务实例时卡住

3. **建议修复**:
   - 在后台任务中添加更多日志，确认执行到哪一步
   - 检查 `get_llm_service()` 是否阻塞
   - 考虑使用 `asyncio.create_task()` 时添加异常处理
   - 测试使用 POST 端点而非 GET 端点

---

## 测试结论

**P1 图片上传测试：部分通过**

- 图片上传功能：✅ 正常
- OCR 识别功能：✅ 正常
- 文本提取功能：✅ 正常
- PPT 生成功能：❌ SSE 流式响应卡住

**建议**: 优先修复 SSE 流式响应问题，该问题影响所有生成场景（不仅是图片上传）。

---

## 给下一个会话的提醒

1. 需要调试后端 `ppt.py` 中的 `generate_full_ppt_stream_get` 函数
2. 检查 LLM 服务调用是否正常（可能是 API Key 或网络问题）
3. 考虑使用 POST 端点 `/api/v1/ppt/generate-stream` 代替 GET 端点测试
4. 可以在后台任务中添加 `print()` 或日志来跟踪执行进度
