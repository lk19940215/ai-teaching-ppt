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
