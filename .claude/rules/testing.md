---
globs: "**/tests/**, **/test-*, **/*.test.*, **/record/**"
---

# 测试规则

## 工具选型

- 浏览器测试步骤 <5 步: 用 Playwright MCP
- 浏览器测试步骤 ≥5 步: 优先用 Playwright CLI（`@playwright/cli`），节省 4x token
- 代码级检查: 用 Shell（lint, type check, pytest）

## Token 预算

- 每个操作后不要都 snapshot，合并 2-3 个操作后再 snapshot
- 长等待（PPT 生成）使用 `browser_wait_for` 而非轮询 snapshot
- 失败时只做 1 次 snapshot + 1 次 console_messages，然后停止该场景
- 详细规则见 `.claude-coder/token-budget-rules.md`

## 测试优先级

1. **P0（必测）**: 文字输入 → 生成 PPT → 下载
2. **P1（必测）**: API Key 缺失/无效错误处理, 参数选择
3. **P2（按需）**: 多学科生成, 图片/PDF 上传
4. **P3（低优先）**: 历史记录, 设置页

## 测试行为规范

- 必须用浏览器交互验证，禁止用代码审查替代
- 测试数据用贴近真实教学的内容（见 `.claude-coder/testing-rules.md` 测试数据）
- 测试失败先分析根因，不要修改测试让它通过
- 每个测试场景独立，不依赖其他场景的结果
- 结果写入 `record/` 目录

## 等待策略

| 操作类型 | 等待方式 |
|---------|---------|
| 导航/点击/填写 | 直接操作，不等待 |
| 表单提交/API | `browser_wait_for` timeout=10s |
| PPT 生成 | `browser_wait_for text="PPT 预览" timeout=180000` |
| 超时判定 | 180 秒无变化 = 失败 |

## 凭证

- 不要修改 `.claude-coder/playwright-auth.json`
- MCP 通过 `--storage-state` 自动注入 API Key
- 凭证失效时记录到报告，提示用户更新

## 测试模板

详细场景模板见 `.claude-coder/test-seed.md`
高效测试策略见 `.claude-coder/efficient-testing-strategy.md`
