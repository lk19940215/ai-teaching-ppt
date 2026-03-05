# Token 预算与成本控制规则

> **适用范围**: 所有使用 AI Agent（Claude Code / claude-coder / Cursor）进行自动化测试和开发的场景
> **核心目标**: 在保证测试质量的前提下，将每次 session 的 token/API 调用量控制在合理范围内
> **参考文献**: AgentAssay (arXiv:2603.02601), Playwright CLI vs MCP Token Analysis (2026.02)

---

## 一、Token 消耗基准数据

### 1.1 Playwright MCP vs CLI

| 指标 | Playwright MCP | Playwright CLI |
|------|---------------|----------------|
| 每个测试 token 消耗 | ~114,000 | ~27,000 |
| 效率比 | 1x | **4x** |
| 每次 snapshot 返回数据 | 50KB-500KB accessibility tree | 文件路径引用 |
| 工具 schema 加载 | 26+ 工具完整 JSON schema | --help 按需发现 |
| 适合场景 | 短测试、需要丰富 DOM 推理 | 长流程、多步骤自动化 |

### 1.2 常见操作 Token 消耗估算

| 操作 | 估算 token |
|------|-----------|
| browser_navigate + browser_snapshot | ~3,000-8,000 |
| browser_fill + browser_snapshot | ~2,000-5,000 |
| browser_click + browser_snapshot | ~2,000-5,000 |
| 完整 E2E 测试（10 步 MCP） | ~80,000-120,000 |
| 完整 E2E 测试（10 步 CLI） | ~20,000-30,000 |
| 代码阅读 + 理解（500 行文件） | ~5,000-10,000 |
| 代码修改 + 验证 | ~10,000-20,000 |

---

## 二、Session 预算上限

### 2.1 Coding Plan 订阅预算分配

即使订阅了 Coding Plan，每月的调用量仍有上限。建议按以下比例分配：

```
每月总预算 100%
├── 功能开发: 60%（核心产出）
├── 测试验证: 25%（质量保障）
├── 调试修复: 10%（问题定位）
└── 文档/探索: 5%（知识积累）
```

### 2.2 单次 Session 预算上限

| Session 类型 | 建议 token 上限 | 建议 API 调用次数上限 |
|-------------|---------------|-------------------|
| 功能实现（小功能） | 200K | 30 次 |
| 功能实现（大功能） | 500K | 60 次 |
| 测试执行（Smoke） | 150K | 20 次 |
| 测试执行（Full E2E） | 400K | 50 次 |
| 代码审查 | 100K | 15 次 |
| Bug 修复 | 300K | 40 次 |

### 2.3 超预算处理

当 token 消耗接近上限时：
1. **立即停止探索性操作**（浏览页面、读无关代码）
2. **优先完成当前任务**，写入 progress.txt
3. **记录未完成项**到 session_result.json
4. **不要强行完成**所有计划的测试用例

---

## 三、分层测试策略（Token 最优）

### 3.1 测试金字塔

```
          ▲
         /  \          E2E Smoke（最贵 ~100K tokens/次）
        / 🔴 \         频率: 每个重大功能完成后 | 每日 1 次
       /------\
      /  🟡    \       Integration（中等 ~30K tokens/次）
     / 集成测试  \      频率: 每个功能完成后
    /------------\
   /   🟢 单元    \     Unit（最便宜 ~5K tokens/次）
  / 单元测试/代码检查\   频率: 每次代码修改后
 /------------------\
```

### 3.2 各层测试策略

#### 🟢 底层：代码级验证（每次修改后 | ~5K tokens）

**执行方式**: 不需要浏览器，用 Shell 命令
```
- 运行 linter: pnpm lint / ruff check
- 运行类型检查: pnpm tsc --noEmit / mypy
- 运行现有单元测试: pnpm test / pytest tests/
```

**token 成本**: 极低（仅 Shell 输出）
**规则**: 每次代码修改后必须执行，这是最低成本的质量门

#### 🟡 中层：功能验证（每个功能后 | ~30K tokens）

**执行方式**: Playwright CLI 或 MCP（有限步骤）
```
- 只验证 Happy Path（正常流程能走通）
- 最多 5 个 Playwright 动作
- 只做 1 次 snapshot 验证结果
```

**token 优化技巧**:
- 用 Playwright CLI 替代 MCP → 节省 4x
- 合并操作：navigate → fill → click → wait_for → snapshot（5步≈15K tokens）
- 跳过中间 snapshot，只在最终结果处验证

#### 🔴 顶层：全流程 E2E（重大节点 | ~100K tokens）

**触发条件**（仅在以下情况执行）:
- 核心生成流程有代码变更
- 发版前
- 用户明确要求
- 连续 3+ 个功能完成后的批量回归

**执行方式**: 完整 test-seed.md 场景
**token 优化技巧**:
- 优先执行 P0 场景（数学 PPT 生成），P1 以下按需执行
- 如果 P0 通过，P1/P2 可以在下次 session 执行

---

## 四、Token 节省铁律

### 4.1 必须遵守的规则

| # | 规则 | 节省估算 |
|---|------|---------|
| 1 | **不要每个操作都 snapshot** — 合并 2-3 个操作后再 snapshot | 40-60% snapshot 成本 |
| 2 | **优先用 CLI 而非 MCP**（长流程 >5 步时） | 75% 测试成本 |
| 3 | **代码审查先于浏览器测试** — 先读代码确认逻辑，再用浏览器验证 | 避免无效测试 |
| 4 | **不要反复读相同文件** — 首次读取后记住关键信息 | 50%+ 文件读取成本 |
| 5 | **截断长输出** — Shell 命令用 `head -n 50` 限制输出 | 防止单次 >10K tokens |
| 6 | **跳过已验证的功能** — 上次 session 通过的测试不重复执行 | 100% 重复测试成本 |
| 7 | **测试数据复用** — 不要每次都重新生成 PPT，可以用已有数据验证 | 避免 LLM 重复调用 |

### 4.2 反模式（禁止）

| 反模式 | 问题 | 替代方案 |
|--------|------|---------|
| 每步都 `browser_snapshot` | 每次 3-8K tokens，10 步 = 30-80K | 关键节点才 snapshot |
| 用 MCP 做 20+ 步的长流程 | 轻松超过 200K tokens | 用 Playwright CLI |
| 反复 navigate 同一页面 | 每次 3-8K tokens | 在同一页面完成所有操作 |
| 读取整个大文件 (>500行) | 一次 10K+ tokens | 用 grep/search 定位再读取片段 |
| 失败后无目标地重试 | 每次重试完整消耗 | 先分析日志，定向修复 |
| 生成 PPT 测试时每次都等 LLM | 单次 PPT 生成 60-180s + tokens | Smoke 测试用已有 PPT 验证预览/下载 |

---

## 五、Trace-First 思想（AgentAssay 启发）

### 5.1 核心思想

不必每次都用 AI Agent 执行测试。可以：
1. **录制一次完整的测试轨迹**（动作序列 + 页面状态）
2. **后续变更后复用轨迹**，只在关键断点重新验证
3. **离线分析轨迹**检测行为回归，零额外 API 调用

### 5.2 在 claude-coder 中的应用

```
首次测试（完整执行）:
├── 执行 test-seed.md 全部场景
├── 记录每步的 snapshot 内容到 record/trace_baseline.md
└── 标记为 baseline

后续回归（增量验证）:
├── 只对变更代码涉及的页面执行 Playwright 测试
├── 对比 snapshot 与 baseline 的差异
└── 无差异 = PASS，有差异 = 人工审查
```

### 5.3 实践规则

- 每次完整 E2E 测试后，将关键 snapshot 内容记录到 `record/trace_baseline.md`
- 后续回归测试先读 baseline，只验证有变更的部分
- 未变更的功能标记为 `SKIP (baseline verified)`

---

## 六、与 tasks.json 的集成

### 6.1 测试任务的预算标注

在 tasks.json 中编写测试任务时，建议标注预算：

```json
{
  "id": "feat-xxx",
  "description": "功能 X 端到端测试",
  "budget": {
    "max_tokens": 150000,
    "max_playwright_actions": 15,
    "test_tier": "smoke"
  },
  "steps": [
    "【预算控制】本任务 token 上限 150K，Playwright 动作上限 15 次",
    "阅读 .claude-coder/token-budget-rules.md 了解成本控制规则",
    "按分层策略执行 Smoke 级别测试...",
    "如果 token 消耗接近上限，优先记录进度到 session_result.json"
  ]
}
```

### 6.2 测试层级标记

| 标记 | 含义 | 预算 |
|------|------|------|
| `test_tier: "unit"` | 仅代码级检查 | 5K tokens |
| `test_tier: "smoke"` | 快速 Happy Path | 30K tokens |
| `test_tier: "regression"` | 关键路径回归 | 100K tokens |
| `test_tier: "full_e2e"` | 全量场景 | 300K tokens |
| `test_tier: "exploratory"` | AI 自主探索 | 200K tokens |

---

## 七、决策流程图

```
代码变更后，按以下决策执行测试：

1. 是否修改了核心生成逻辑？
   ├── 否 → 只跑 Unit（lint + type check）→ 结束
   └── 是 ↓

2. 修改范围大吗？（>3 个文件 或 >100 行）
   ├── 否 → 跑 Smoke（5步 Playwright，目标功能）→ 结束
   └── 是 ↓

3. 是否发版前？
   ├── 否 → 跑 Regression（核心路径 × 2-3 场景）→ 结束
   └── 是 → 跑 Full E2E（test-seed.md 全量）→ 结束
```
