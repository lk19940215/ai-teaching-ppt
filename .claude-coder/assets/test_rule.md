# Playwright 自动化测试通用规则 v0.0.1

## 一、四条铁律

1. **真实操作** — 必须通过 Playwright MCP 产生浏览器交互，代码审查不等于测试
2. **测试业务** — 断言基于用户可见结果（页面文本、按钮状态），非内部变量
3. **独立可重复** — 每个场景不依赖其他测试结果
4. **先调查再修复** — 失败先分析根因，不要修改测试让它通过

## 二、三步测试方法论

任何 Web 项目的端到端测试遵循三步走：

### Step 1: 功能验证（Happy Path）

核心用户流程能走通，每个步骤对应一个 Playwright MCP 工具调用：

```
1. browser_navigate → [页面URL]
2. browser_snapshot → 确认页面加载，定位关键元素 ref
3. browser_fill_form / browser_type → 输入测试数据
4. browser_click → 提交操作
5. browser_wait_for → 等待结果出现
6. browser_snapshot → 验证预期结果
```

### Step 2: 错误场景（Unhappy Path）

| 类别 | 典型场景 |
|------|---------|
| 输入验证 | 空提交、超长输入、特殊字符、非法格式 |
| 认证权限 | 未登录访问、过期凭证、无效 API Key |
| 网络服务 | 后端宕机、慢响应、API 500 |
| 状态边界 | 空数据、大数据量、重复提交、浏览器后退 |

### Step 3: 探索性测试

以目标用户角色自由使用系统，关注可发现性、可理解性、响应速度、错误恢复、视觉一致性。

## 三、Playwright MCP 工具速查

### 导航与观察

| 工具 | 用途 | 关键参数 |
|------|------|---------|
| `browser_navigate` | 打开页面 | `url` |
| `browser_snapshot` | 获取页面可访问性快照 | 无 |
| `browser_console_messages` | 检查控制台 | `level` |
| `browser_network_requests` | 网络请求日志 | 无 |

### 交互操作

| 工具 | 用途 | 关键参数 |
|------|------|---------|
| `browser_click` | 点击元素 | `ref`, `element` |
| `browser_type` | 逐字符输入 | `ref`, `text`, `submit` |
| `browser_fill_form` | 批量填写表单 | `fields[]` |
| `browser_select_option` | 选择下拉项 | `ref`, `values[]` |
| `browser_press_key` | 按键 | `key` |
| `browser_file_upload` | 上传文件 | `paths[]` |
| `browser_handle_dialog` | 处理弹窗 | `accept` |

### 等待与控制

| 工具 | 用途 | 关键参数 |
|------|------|---------|
| `browser_wait_for` | 等待元素/文本出现 | `text`, `ref`, `timeout` |
| `browser_evaluate` | 执行 JS | `function` |
| `browser_close` | 关闭页面 | 无 |

## 四、Smart Snapshot 策略（节省 40-60% Token）

每次 `browser_snapshot` 消耗 3,000-8,000 tokens。分级控制：

| 级别 | 何时 snapshot | 示例 |
|------|-------------|------|
| **必须** | 首次加载页面 | navigate 后确认页面正确 |
| **必须** | 关键断言点 | 验证操作结果出现 |
| **必须** | 操作失败时 | 调查页面状态 |
| **可选** | 中间操作后 | fill 后确认文字填入 |
| **跳过** | 连续同类操作间 | 连续选择多个下拉框 |
| **跳过** | 等待循环中 | 改用 `browser_wait_for` |

**高效模式**：navigate → snapshot → fill → select → click → wait_for → snapshot（**2 次**）
**低效模式**：navigate → snapshot → fill → snapshot → select → snapshot → click → snapshot（**4 次**）

## 五、等待策略

### 按操作类型选择

| 操作类型 | 策略 | Token 消耗 |
|---------|------|-----------|
| 瞬时（导航、点击） | 直接操作，不等待 | 极低 |
| 短等（表单提交） | `browser_wait_for text="成功" timeout=10000` | ~5K |
| 长等（AI 生成、文件处理） | `browser_wait_for` + 合理 timeout | ~5K |
| 超长等（批量处理） | Shell 端 API 检查 + 最终 1 次 snapshot | ~5.5K |

### SSE / 流式生成任务的等待策略

当操作涉及 AI 生成、文件转换、SSE 流式处理等需要较长时间的场景时，优先使用 `browser_wait_for` 而非轮询 snapshot：

| 步骤 | 工具 | 说明 |
|------|------|------|
| 触发操作 | `browser_click` | 点击"生成"/"提交"按钮 |
| 等待完成 | `browser_wait_for` | 等待完成标志文本出现，设置合理 timeout |
| 验证结果 | `browser_snapshot` | 确认结果/下载链接出现 |

**`browser_wait_for` 参数**：
- `text`：完成标志文本（如"下载"、"完成"、"预览"）
- `timeout`：根据操作实际预估耗时设置（如表单提交 10s、AI 生成 60-180s、批量处理更长）
- 相比轮询 snapshot，Token 消耗从 ~60K+ 降至 ~5K

### 常见反模式

- 每步 snapshot → 合并 2-3 操作后再 snapshot
- 轮询 snapshot 等待长操作 → 改用 `browser_wait_for`
- MCP 做 20+ 步 → 长流程用 Playwright CLI
- 反复 navigate 同一页面 → 在同一页面完成
- 失败后盲目重试 → 先 `browser_console_messages` 分析

### 优先级映射

P0（核心流程）必测 → P1（错误处理）必测 → P2（次要功能）按需 → P3 低优先

预算 >200K: P0+P1+P2 | 100-200K: P0+P1 | <100K: 仅 P0

## 六、凭证管理

`.mcp.json` 由 `claude-coder auth` 自动生成，根据配置模式使用不同参数：
- persistent（默认）：`--user-data-dir=<path>`，登录态自动保持
- isolated：`--isolated --storage-state=<path>`，每次从快照加载
- extension：`--extension`，连接真实浏览器

凭证失效时：不修改 auth 文件，报告中标注，提示用户运行 `claude-coder auth [URL]`。

## 七、失败处理

**阻断性**（立即停止）: 服务未启动、500 错误、凭证缺失、页面空白

**非阻断性**（记录继续）: 样式异常、console warning、慢响应

失败时: snapshot（记录状态）→ console_messages（错误日志）→ 停止该场景 → 继续下一个

## 八、tasks.json 测试步骤模板

推荐使用结构化标签前缀（`【规则】【环境】【P0】` 等）组织步骤。研究表明，结构化标记可提升 LLM 的指令遵循度和步骤完成率，帮助 Agent 理解每步的目的和优先级。

### 基础模板

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

### 含长等待操作的模板（SSE / AI 生成 / 文件转换）

```json
{
  "steps": [
    "【规则】阅读 .claude-coder/test_rule.md",
    "【环境】curl http://localhost:8000/health 确认后端服务正常",
    "【P0】Playwright MCP 访问目标页面，snapshot 确认页面加载",
    "【P0】填写表单数据，snapshot 确认输入成功",
    "【P0】点击提交，使用 browser_wait_for 等待结果出现（根据操作耗时设置合理 timeout）",
    "【P0】验证结果正确（下载链接有效 / 预览内容匹配）",
    "【记录】测试结果写入 record/（使用 test_rule.md 报告模板）",
    "【预算】Smart Snapshot 策略：导航→填写→点击→等待→验证，共 3-4 次 snapshot"
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