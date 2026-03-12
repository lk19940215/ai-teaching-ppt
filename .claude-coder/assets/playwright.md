【Playwright MCP 规则提醒】

## Smart Snapshot 策略（节省 40-60% Token）
- 必须：首次加载页面、关键断言点、操作失败时
- 跳过：连续同类操作间、等待循环中（改用 browser_wait_for）
- 高效模式：navigate → snapshot → fill → select → click → wait_for → snapshot（仅 2 次）

## 等待策略
- 瞬时操作（导航、点击）：直接操作，不等待
- 短等（表单提交）：browser_wait_for text="成功" timeout=10000
- 长等（AI 生成、SSE 流式、文件处理）：browser_wait_for + 合理 timeout（60-180s）
- 禁止轮询 snapshot 等待，Token 消耗从 ~60K+ 降至 ~5K

## 失败处理
- 阻断性（服务未启动、500 错误、凭证缺失）：立即停止
- 非阻断性（样式异常、console warning）：记录后继续
- 失败流程：snapshot（记录状态）→ console_messages（错误日志）→ 停止该场景