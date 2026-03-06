# Playwright 自动化测试通用规则 v0.0.1

> AI Agent 执行端到端测试前必读。本文件由 claude-coder 自动部署。

---

## 一、四条铁律

1. **真实操作** — 必须通过 Playwright MCP 产生浏览器交互，代码审查不等于测试
2. **测试业务** — 断言基于用户可见结果（页面文本、按钮状态），非内部变量
3. **独立可重复** — 每个场景不依赖其他测试结果
4. **先调查再修复** — 失败先分析根因，不要修改测试让它通过

---

## 二、三步测试法

**Step 1 — Happy Path**: navigate → snapshot → 输入 → 操作 → wait_for → snapshot 验证

**Step 2 — 错误场景**: 空提交、无效凭证、后端宕机、重复提交

**Step 3 — 探索性测试**: 以目标用户角色自由操作，记录所有"不符合直觉"的交互

---

## 三、Smart Snapshot（节省 40-60% Token）

每次 `browser_snapshot` 消耗 3K-8K tokens，**必须分级控制**：

| 何时 snapshot | 何时跳过 |
|-------------|---------|
| 首次加载页面 | 连续同类操作间（连续填多个字段） |
| 关键断言点（验证结果） | 等待循环中（改用 `browser_wait_for`） |
| 操作失败时 | 中间过渡操作 |

**高效**: navigate → snapshot → fill → select → click → wait_for → snapshot（**2 次**）
**低效**: 每步都 snapshot（**6 次** = 30K+ tokens 浪费）

---

## 四、等待策略

| 操作类型 | 策略 |
|---------|------|
| 瞬时（导航、点击） | 直接操作 |
| 短等（表单提交） | `browser_wait_for text="成功" timeout=10000` |
| 长等（AI 生成） | 指数退避: 10s → 30s → 60s → 120s → 超时 |
| 超长等 | Shell: `curl API/status` + 最终 1 次 snapshot |

**禁止**: 每 10 秒轮询 snapshot（180s = 18 次 = ~90K tokens）

---

## 五、Token 预算

### 分层策略

| 层级 | 执行方式 | Token | 频率 |
|------|---------|-------|------|
| Unit | Shell: lint + test | ~5K | 每次修改 |
| Smoke | Playwright ≤5 步 | ~30K | 每个功能 |
| Full E2E | 全场景 | ~100K+ | 发版前 |

### 禁止的反模式

- 每步 snapshot → 合并 2-3 操作后再 snapshot
- MCP 做 20+ 步 → 长流程用 Playwright CLI
- 反复 navigate 同一页面 → 在同一页面完成
- 失败后盲目重试 → 先 `browser_console_messages` 分析

### 优先级映射

P0（核心流程）必测 → P1（错误处理）必测 → P2（次要功能）按需 → P3 低优先

预算 >200K: P0+P1+P2 | 100-200K: P0+P1 | <100K: 仅 P0

---

## 六、凭证管理

`.mcp.json` 配置 `--isolated --storage-state=path/to/auth.json`。

**关键**: `--storage-state` **必须**配合 `--isolated`，否则 localStorage 不注入。

凭证失效时：不修改 auth 文件，报告中标注，提示用户运行 `claude-coder auth [URL]`。

---

## 七、失败处理

**阻断性**（立即停止）: 服务未启动、500 错误、凭证缺失、页面空白

**非阻断性**（记录继续）: 样式异常、console warning、慢响应

失败时: snapshot（记录状态）→ console_messages（错误日志）→ 停止该场景 → 继续下一个

---

## 八、tasks.json 测试步骤模板

```json
{
  "steps": [
    "【规则】阅读 .claude-coder/test_rule.md",
    "【环境】curl [后端]/health && curl [前端]（失败则停止）",
    "【P0】Playwright MCP 执行核心 Happy Path（Smart Snapshot）",
    "【P1】错误场景：空输入、无效凭证",
    "【记录】结果写入 record/",
    "【预算】消耗 >80% 时跳过低优先级，记录 session_result.json"
  ]
}
```

## 九、测试报告格式

```markdown
# E2E 测试报告
**日期**: YYYY-MM-DD | **环境**: 前端 [URL] / 后端 [URL]

| 场景 | 结果 | 备注 |
|------|------|------|
| [名称] | PASS/FAIL | [简要] |

## 发现的问题
### [P0/P1/P2] 标题
- **复现**: [Playwright 动作序列]
- **预期/实际**: ...
- **根因**: [代码分析]
```
