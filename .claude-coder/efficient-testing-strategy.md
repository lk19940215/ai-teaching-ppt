# AI Agent 高效测试策略

> **适用范围**: AI Agent（Claude Code / claude-coder）执行自动化测试时的效率优化
> **核心目标**: 用最少的交互次数达到最高的缺陷发现率
> **依赖文档**: token-budget-rules.md（成本控制）, testing-rules.md（行为规范）, test-seed.md（场景模板）

---

## 一、核心理念：测试 ROI 最大化

### 1.1 测试的目标不是覆盖率，而是缺陷发现率

传统测试追求"100% 覆盖率"，但 AI Agent 测试的成本与覆盖率呈指数关系：

```
覆盖率  Token 成本    缺陷发现率
 50%     ~50K         发现 80% 的 P0/P1 缺陷
 70%     ~120K        发现 90% 的 P0/P1 缺陷
 90%     ~350K        发现 95% 的 P0/P1 缺陷
100%     ~800K+       发现 98% 的 P0/P1 缺陷
```

**策略**: 瞄准 50-70% 覆盖率，用最优的 50K-120K tokens 捕获 80-90% 的关键缺陷。

### 1.2 帕累托法则（80/20 原则）

- **20% 的代码**产生 **80% 的 bug**（通常是核心流程、边界处理、状态转换）
- **20% 的测试场景**能发现 **80% 的问题**（通常是 Happy Path + 空输入 + 权限错误）
- 优先测试这 20% 的高价值场景

---

## 二、Smart Snapshot 策略

### 2.1 问题：Snapshot 是最大的 Token 消耗源

每次 `browser_snapshot` 返回完整的 accessibility tree，消耗 3,000-8,000 tokens。一个 10 步测试如果每步都 snapshot，仅 snapshot 就消耗 30,000-80,000 tokens。

### 2.2 解决方案：分级 Snapshot

| 级别 | 何时 snapshot | 示例 |
|------|-------------|------|
| **必须** | 首次加载页面 | navigate 后确认页面正确 |
| **必须** | 关键断言点 | 验证 PPT 生成结果出现 |
| **必须** | 操作失败时 | 按钮点不了、页面无反应 |
| **可选** | 中间操作后 | fill 后确认文字填入 |
| **跳过** | 连续同类操作间 | 连续选择年级、学科、风格 |
| **跳过** | 等待循环中的每次检查 | 改为检查特定文本/元素 |

### 2.3 批量操作模式

**低效模式**（6 次 snapshot ≈ 30K tokens）：
```
navigate → snapshot → fill → snapshot → select → snapshot → 
select → snapshot → click → snapshot → wait → snapshot
```

**高效模式**（2 次 snapshot ≈ 10K tokens）：
```
navigate → snapshot（确认页面）→ fill → select → select → 
click → wait_for("生成结果") → snapshot（验证结果）
```

**规则**: 
- 页面加载后 1 次 snapshot
- 中间操作不 snapshot（除非操作复杂或可能失败）
- 最终结果 1 次 snapshot
- 失败时补 1 次 snapshot + console_messages

---

## 三、测试优先级排序

### 3.1 场景优先级矩阵

按 **风险 × 频率** 排序，决定测试执行顺序：

| 优先级 | 风险 | 使用频率 | 示例 | 是否必测 |
|--------|------|---------|------|---------|
| P0 | 高 | 高 | 文字输入 → 生成 PPT → 下载 | **必测** |
| P1 | 高 | 中 | API Key 缺失/无效时的错误处理 | 必测 |
| P1 | 中 | 高 | 年级/学科/风格参数选择 | 必测 |
| P2 | 中 | 中 | 英语学科专属生成逻辑 | 按需 |
| P2 | 中 | 低 | 图片/PDF 上传 → OCR → 生成 | 按需 |
| P3 | 低 | 中 | 历史记录查看/下载 | 按需 |
| P3 | 低 | 低 | 设置页面 UI 交互 | 低优先 |

### 3.2 执行策略

```
Session 预算充足（>200K tokens）:
  → P0 + P1 + P2

Session 预算一般（100-200K tokens）:
  → P0 + P1

Session 预算紧张（<100K tokens）:
  → 仅 P0
```

### 3.3 渐进式测试

不要一次执行所有场景。按 session 分散：

```
Session 1: P0（核心生成流程）
Session 2: P1（错误处理 + 参数校验）
Session 3: P2（多学科 + 上传流程）
Session 4: P3 + 探索性测试
```

---

## 四、高效等待策略

### 4.1 问题：PPT 生成需要 60-180 秒

LLM 生成 PPT 内容是最慢的操作。如果每 10 秒 snapshot 一次，180 秒需要 18 次 snapshot = 54,000-144,000 tokens，极其浪费。

### 4.2 解决方案：智能等待

**方案 A：使用 `browser_wait_for`**（推荐）
```
browser_click → 点击生成按钮
browser_wait_for text="PPT 预览" timeout=180000
browser_snapshot → 验证结果
```
Token 消耗：仅 1 次 snapshot ≈ 5,000 tokens

**方案 B：指数退避轮询**
```
点击生成后：
  10s → snapshot（检查是否有进度条）
  20s → 无需 snapshot（刚看过）
  40s → snapshot（检查进度变化）
  80s → snapshot（应该快完成了）
  120s → snapshot（最后检查）
  180s → 超时判定
```
Token 消耗：4 次 snapshot ≈ 20,000 tokens（比每 10 秒好 4.5x）

**方案 C：shell 端检查（零 snapshot 成本）**
```
通过 Shell 命令检查后端日志或 API 状态：
  curl -s http://localhost:8000/api/v1/generate/status/{task_id}
  如果返回 completed → 再做 1 次 browser_snapshot 验证
```
Token 消耗：Shell 输出 ≈ 500 tokens + 1 次 snapshot ≈ 5,500 tokens

### 4.3 等待策略决策树

```
操作类型是什么？
├── 瞬时（导航、点击、填写）→ 直接操作，不等待
├── 短等（提交表单、API 验证）→ wait_for + 1 次 snapshot
├── 长等（PPT 生成、文件处理）→ 指数退避 或 Shell 端检查
└── 超长等（批量处理）→ Shell 端检查 + 最终 1 次 snapshot
```

---

## 五、失败快速反馈机制

### 5.1 Early Exit 原则

测试中遇到阻断性错误时，立即停止后续测试，避免浪费 token：

```
阻断性错误（立即停止）:
├── 前/后端服务未启动
├── 页面返回 500 错误
├── API Key 完全缺失
└── 核心页面空白

非阻断性错误（记录继续）:
├── 某个按钮样式异常
├── 控制台有 warning
├── 响应较慢但最终成功
└── 非核心功能不可用
```

### 5.2 失败后的 Token 节省策略

```
测试失败时：
1. 执行 1 次 browser_snapshot（记录当前状态）
2. 执行 1 次 browser_console_messages（获取错误日志）
3. 停止该场景的后续步骤
4. 将失败信息写入 record/
5. 继续下一个独立场景（如果有预算）

禁止：
- 反复重试失败的步骤（除非改了代码）
- 用多种方式尝试同一个操作
- 在失败状态下继续执行依赖该功能的后续场景
```

---

## 六、测试结果缓存与复用

### 6.1 测试结果缓存

每次测试结果记录到 `record/test_cache.json`：

```json
{
  "last_run": "2026-03-05T10:00:00",
  "results": {
    "scene_a_math_ppt": {
      "status": "pass",
      "last_pass": "2026-03-05T10:00:00",
      "code_hash": "abc123",
      "skip_until_code_change": true
    },
    "scene_c1_empty_input": {
      "status": "pass",
      "last_pass": "2026-03-05T10:05:00",
      "code_hash": "def456",
      "skip_until_code_change": true
    }
  }
}
```

### 6.2 跳过已验证的场景

后续 session 执行测试时：
1. 读取 `record/test_cache.json`
2. 对比当前代码的 git diff 与缓存的 `code_hash`
3. 如果相关代码未变更 → **跳过**，标记为 `SKIP (cached pass)`
4. 如果代码有变更 → 重新执行

---

## 七、Playwright 工具选型矩阵

### 7.1 何时用 MCP vs CLI

| 场景 | 推荐工具 | 原因 |
|------|---------|------|
| 功能验证（<5 步） | MCP | 设置简单，步骤少时差异不大 |
| 功能验证（>5 步） | CLI | 节省 4x token |
| 错误场景测试 | MCP | 步骤少，需要精确 DOM 推理 |
| 探索性测试 | CLI | 步骤多，上下文压力大 |
| 截图对比/视觉验证 | MCP (--caps=vision) | 需要视觉模型 |
| 回归测试（多场景） | CLI | 总 token 量大，必须节省 |
| 首次搭建测试 | MCP | 交互式调试方便 |

### 7.2 混合使用策略

```
推荐的工作流程：
1. 首次开发测试 → 用 MCP（交互式调试，建立 baseline）
2. 后续回归测试 → 切换到 CLI（token 友好）
3. 发现问题时 → 切回 MCP（精确定位）
```

---

## 八、与 claude-coder 工作流的集成

### 8.1 6 步工作流中的测试位置

```
claude-coder 6 步工作流:
1. 恢复上下文
2. 环境检查
3. 选择任务
4. 增量实现 ← 代码变更发生在这里
5. 测试验证 ← 本文档的策略在这里应用
6. 收尾

Step 5 的执行逻辑:
├── 检查 Step 4 变更了哪些代码
├── 读取 token-budget-rules.md 决定测试层级
├── 读取 test_cache.json 跳过已验证场景
├── 按优先级执行测试
├── 写入结果到 record/ 和 test_cache.json
└── 超预算时写入 session_result.json 标记未完成测试
```

### 8.2 tasks.json 测试步骤模板

```json
{
  "steps": [
    "【效率规则】阅读 .claude-coder/efficient-testing-strategy.md",
    "【预算控制】阅读 .claude-coder/token-budget-rules.md，本任务 tier=smoke",
    "【缓存检查】读取 record/test_cache.json，跳过已通过且代码未变更的场景",
    "【环境检查】curl localhost:8000/health && curl localhost:3000（失败则停止）",
    "【P0 测试】执行 test-seed.md 场景 A（数学 PPT 生成），使用 Smart Snapshot",
    "【结果记录】更新 record/test_cache.json 和 record/e2e_test_results.md",
    "【预算检查】如果已消耗 >80% 预算，跳过 P1 以下测试，记录到 session_result.json"
  ]
}
```
