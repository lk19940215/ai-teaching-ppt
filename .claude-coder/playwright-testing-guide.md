# Playwright 自动化测试通用指南（MCP + CLI）

> **适用范围**: 任何 Web 项目（前后端分离、SPA、SSR 均适用）
> **使用方式**: AI Agent 阅读本文档后，结合项目代码，自动生成并执行端到端测试
> **版本**: 基于 @playwright/mcp@latest + @playwright/cli@latest (2026.03)
> **成本控制**: 配合 `token-budget-rules.md` 和 `efficient-testing-strategy.md` 使用

---

## 第一部分：Playwright MCP 工具完整清单

### 1.1 导航类

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_navigate` | `url` (string, 必填) | 导航到指定 URL |
| `browser_navigate_back` | 无 | 浏览器后退 |
| `browser_navigate_forward` | 无 | 浏览器前进 |

**示例**:
```
browser_navigate url="http://localhost:3000/login"
```

### 1.2 页面观察类

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_snapshot` | 无 | 获取页面可访问性快照（核心工具，返回结构化 DOM 树） |
| `browser_take_screenshot` | 无 | 截取页面图片（仅在 --caps=vision 启用时可用） |
| `browser_console_messages` | `level` (error/warning/info/debug) | 获取浏览器控制台消息 |
| `browser_network_requests` | 无 | 获取网络请求日志 |

**snapshot 返回示例**:
```
- heading "登录" [level=1]
- textbox "用户名" [ref=E3]
- textbox "密码" [ref=E5]  
- button "登录" [ref=E7] [disabled]
```

> **核心原则**: 优先使用 `browser_snapshot`（轻量、结构化），而非 `browser_take_screenshot`（重、需视觉模型）。

### 1.3 交互类

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_click` | `ref` (string, 必填), `element` (string), `doubleClick` (bool), `button` (left/right/middle), `modifiers` (array) | 点击元素 |
| `browser_type` | `ref` (string, 必填), `text` (string, 必填), `submit` (bool) | 在可编辑元素中输入文本（逐字符输入，适合搜索框联想） |
| `browser_fill_form` | `fields` (array, 必填) | 批量填写表单字段 |
| `browser_select_option` | `ref` (string, 必填), `values` (array, 必填) | 选择下拉框选项 |
| `browser_hover` | `ref` (string, 必填), `element` (string) | 悬停在元素上 |
| `browser_drag` | `startRef`, `endRef` (string, 必填) | 拖拽元素 |
| `browser_press_key` | `key` (string, 必填), `ref` (string) | 按键（Enter/Tab/Escape/ArrowDown 等） |
| `browser_handle_dialog` | `accept` (bool, 必填), `promptText` (string) | 处理弹窗（alert/confirm/prompt） |
| `browser_file_upload` | `paths` (array) | 上传文件 |

**交互示例**:
```
browser_click ref="E7" element="登录按钮"
browser_type ref="E3" text="admin@example.com" submit=false
browser_select_option ref="E12" values=["option_value"]
browser_press_key key="Enter"
browser_file_upload paths=["/path/to/test.png"]
```

### 1.4 JavaScript 执行

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_evaluate` | `function` (string, 必填), `ref` (string) | 在页面执行 JS 代码 |

**常用场景**:
```
// 读取 localStorage
browser_evaluate function="() => localStorage.getItem('token')"

// 清除 localStorage
browser_evaluate function="() => localStorage.clear()"

// 获取当前 URL
browser_evaluate function="() => window.location.href"

// 滚动到底部
browser_evaluate function="() => window.scrollTo(0, document.body.scrollHeight)"

// 获取元素数量
browser_evaluate function="() => document.querySelectorAll('.item').length"
```

### 1.5 浏览器控制类

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_close` | 无 | 关闭页面 |
| `browser_resize` | `width`, `height` (number, 必填) | 调整浏览器窗口大小 |
| `browser_tab_list` | 无 | 列出所有标签页 |
| `browser_tab_new` | `url` (string) | 新开标签页 |
| `browser_tab_select` | `index` (number, 必填) | 切换标签页 |
| `browser_tab_close` | `index` (number) | 关闭标签页 |

### 1.6 等待类

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_wait_for` | `text` (string), `ref` (string), `timeout` (number) | 等待元素出现或文本出现 |

---

## 第二部分：三步测试方法论

### 概述

任何 Web 项目的端到端测试都遵循三步走：

```
Step 1: 功能验证（Happy Path）
  → 核心用户流程能走通吗？

Step 2: 错误场景（Unhappy Path）  
  → 异常输入、断网、权限不足时表现如何？

Step 3: 探索性测试（Discovery）
  → 像真实用户一样自由使用，发现"没想到"的问题
```

### 2.1 Step 1: 功能验证测试

**目标**: 验证每个核心用户故事从头到尾可以走通。

**通用模板**:

```markdown
## 功能验证：[功能名称]

### 前置条件
- [ ] 前端服务运行中（验证方式：curl [前端URL]）
- [ ] 后端服务运行中（验证方式：curl [后端URL]/health）
- [ ] 认证凭证已配置（storageState / cookies / token）

### 测试步骤

| 步骤 | Playwright MCP 动作 | 预期结果 | 失败处理 |
|------|---------------------|----------|----------|
| 1. 打开页面 | browser_navigate url="[URL]" | 页面加载完成 | 检查服务是否启动 |
| 2. 确认页面 | browser_snapshot | 包含 [关键元素] | 检查路由配置 |
| 3. 输入数据 | browser_type ref="[ref]" text="[数据]" | 输入框显示内容 | 检查元素是否可交互 |
| 4. 提交操作 | browser_click ref="[ref]" | 触发后端请求 | 检查按钮是否 disabled |
| 5. 等待结果 | browser_wait_for text="[成功标志]" timeout=30000 | 出现成功提示 | 检查 console_messages |
| 6. 验证结果 | browser_snapshot | 包含 [结果内容] | 记录实际页面内容 |

### 断言标准
- **通过**: [用户可见的成功标志]
- **失败**: [任何错误提示、空白页面、超时]
```

**生成规则（给 AI Agent 的指令）**:

1. 阅读项目的路由文件（如 `app/` 或 `pages/`），列出所有页面
2. 阅读项目的 README 或需求文档，理解核心用户故事
3. 为每个用户故事生成一个功能验证测试
4. 每个步骤必须对应一个 Playwright MCP 工具调用
5. 每个步骤后面必须跟一个 `browser_snapshot` 验证

### 2.2 Step 2: 错误场景测试

**目标**: 验证系统在异常条件下的表现是否友好。

**通用错误场景清单**:

```markdown
## 错误场景清单

### A. 输入验证类
| 场景 | 操作 | 预期 |
|------|------|------|
| 空提交 | 不填任何内容，直接点提交 | 按钮 disabled 或显示验证错误 |
| 超长输入 | 输入超过限制的内容 | 截断或提示字数超限 |
| 特殊字符 | 输入 <script>alert(1)</script> | 正确转义，不执行脚本 |
| 非法格式 | 邮箱框输入非邮箱格式 | 显示格式错误提示 |

### B. 认证与权限类
| 场景 | 操作 | 预期 |
|------|------|------|
| 未登录访问 | 清除凭证后访问受保护页面 | 重定向到登录页或显示提示 |
| 过期凭证 | 使用过期 token | 友好提示重新登录 |
| 无效凭证 | 使用错误的 API Key/密码 | 明确的错误提示（非技术错误栈） |

### C. 网络与服务类
| 场景 | 操作 | 预期 |
|------|------|------|
| 后端宕机 | 关闭后端后操作 | 友好错误提示，非空白页 |
| 慢响应 | 后端延迟 30s+ | 有 loading 状态，不重复提交 |
| 请求失败 | API 返回 500 | 显示用户可理解的错误信息 |

### D. 状态与边界类
| 场景 | 操作 | 预期 |
|------|------|------|
| 空数据 | 列表页无数据 | 显示空状态提示（非空白） |
| 大数据量 | 列表 100+ 条数据 | 分页正常，不卡顿 |
| 重复操作 | 快速连点提交按钮 | 防重复提交，只处理一次 |
| 浏览器后退 | 提交后按后退键 | 不重复提交，状态一致 |
```

**测试模板**:

```markdown
## 错误场景：[场景名称]

### 步骤
1. browser_navigate url="[URL]"
2. [触发错误条件的操作]
   - 清除凭证：browser_evaluate function="() => localStorage.clear()"
   - 输入非法数据：browser_type ref="[ref]" text="[非法输入]"
   - 不填写必填项：直接点击提交
3. browser_snapshot → 检查页面反馈

### 断言
- **通过**: 出现用户友好的错误提示文案
- **失败**: 出现技术错误栈 / 空白页面 / 无任何反馈 / 控制台有未捕获异常
```

### 2.3 Step 3: 探索性测试

**目标**: 不按预设路径，像真实用户一样自由使用系统，发现"没想到"的问题。

**通用模板**:

```markdown
## 探索性测试

### 角色设定
你是 [目标用户角色]，第一次使用这个系统。你的目标是 [业务目标]。

### 规则
1. 从首页开始，不要跳过任何步骤
2. 用 browser_snapshot 观察每个页面，像真实用户一样理解界面
3. 用 browser_click/browser_type 完成你的任务
4. 遇到困惑时，记录下来而不是跳过
5. 关注以下维度：

| 维度 | 观察点 |
|------|--------|
| **可发现性** | 功能入口是否容易找到？ |
| **可理解性** | 按钮文案、提示信息是否清晰？ |
| **响应速度** | 每个操作等待时间是否可接受？ |
| **错误恢复** | 操作失败后能否轻松重试？ |
| **视觉一致性** | 字体、颜色、间距是否统一？ |
| **信息架构** | 导航结构是否合理？ |

### 输出格式
将发现的问题记录到 record/exploratory_test.md：

每个问题包含：
- **问题标题**: 一句话描述
- **严重程度**: P0(阻断) / P1(严重) / P2(一般) / P3(建议)
- **发现路径**: 从哪个页面、点了什么、看到了什么
- **预期行为**: 应该怎样
- **实际行为**: 实际怎样
- **复现步骤**: Playwright MCP 动作序列
- **修复建议**: 代码层面的修改建议
```

---

## 第三部分：AI Agent 测试执行协议

### 3.1 测试生成流程

当 AI Agent 收到"为项目生成测试"的指令时，按以下流程执行：

```
Phase 1: 项目理解（只读）
├── 阅读 README.md 了解项目功能
├── 阅读路由文件了解所有页面
├── 阅读 API 文件了解所有接口
├── 阅读认证逻辑了解凭证管理
└── 输出：项目功能清单 + 页面清单

Phase 2: 测试计划
├── 为每个核心功能设计 Happy Path
├── 为每个输入设计错误场景
├── 设计 2-3 个探索性测试角色
└── 输出：测试计划文档

Phase 3: 测试执行
├── 环境检查（前后端服务、凭证）
├── 按计划逐个执行测试
├── 每个步骤后 browser_snapshot 验证
└── 输出：测试结果报告

Phase 4: 问题修复
├── 分析失败测试的根因
├── 修复代码
├── 用 Playwright MCP 复测
└── 输出：修复提交 + 更新后的测试报告
```

### 3.2 铁律

1. **禁止用代码审查替代浏览器交互测试**
   - 不允许："我看了代码，逻辑正确，通过"
   - 必须："我用 browser_click 点了按钮，browser_snapshot 显示结果正确，通过"

2. **每个操作后必须验证**
   - 不允许：连续执行 5 个动作，最后才 snapshot
   - 必须：每个关键动作后 snapshot，确认状态正确再继续

3. **失败时先调查，后修复**
   - 不允许：测试失败 → 修改测试让它通过
   - 必须：测试失败 → browser_console_messages 检查错误 → 分析根因 → 修复产品代码

4. **测试数据必须有意义**
   - 不允许：输入 "test" / "abc" / "123"
   - 必须：输入贴近真实场景的数据（如真实的邮箱格式、合理的文本内容）

5. **等待必须有策略**
   - 短操作（导航、点击）：操作后立即 snapshot
   - 中等操作（表单提交）：browser_wait_for 等待结果出现，timeout=10000
   - 长操作（文件处理、AI 生成）：轮询 snapshot，每 10 秒一次，最大 timeout 按业务设定

### 3.3 凭证管理

```
方式 1: storageState（推荐）
  .mcp.json 中配置 --isolated --storage-state=path/to/auth.json
  auth.json 包含 cookies + localStorage
  注意：--storage-state 必须配合 --isolated 使用，否则不生效
  适用于：已登录状态的测试

方式 2: 测试中登录
  browser_navigate → 登录页
  browser_type → 输入用户名密码
  browser_click → 点击登录
  browser_wait_for → 等待跳转到首页
  适用于：登录流程本身的测试

方式 3: browser_evaluate 注入
  browser_evaluate function="() => localStorage.setItem('token', 'xxx')"
  browser_navigate → 刷新页面
  适用于：临时注入凭证
```

### 3.4 等待策略速查

| 场景 | 方法 | 参数 |
|------|------|------|
| 等待元素出现 | `browser_wait_for` | `text="成功"` 或 `ref="E15"`, `timeout=10000` |
| 等待页面跳转 | `browser_snapshot` 后检查 URL | 配合 `browser_evaluate` 获取 `location.href` |
| 等待 AJAX 完成 | `browser_network_requests` | 检查请求状态 |
| 轮询等待长任务 | 循环 `browser_snapshot` | 每 N 秒一次，最大 M 次 |

---

## 第四部分：测试报告模板

```markdown
# [项目名] E2E 测试报告

**日期**: YYYY-MM-DD
**工具**: Playwright MCP
**环境**: [前端URL] / [后端URL]

## 摘要

| 类别 | 总数 | 通过 | 失败 | 跳过 |
|------|------|------|------|------|
| 功能验证 | - | - | - | - |
| 错误场景 | - | - | - | - |
| 探索性测试 | - | - 个发现 | - | - |

## 功能验证结果

| 场景 | 结果 | 耗时 | 备注 |
|------|------|------|------|
| [场景名] | PASS/FAIL | Xs | [简要] |

## 错误场景结果

| 场景 | 结果 | 错误处理质量 | 备注 |
|------|------|--------------|------|
| [场景名] | PASS/FAIL | 友好/不友好/无反馈 | [简要] |

## 发现的问题

### [P0/P1/P2/P3] 问题标题

- **发现方式**: 功能验证 / 错误场景 / 探索性测试
- **复现步骤**:
  1. browser_navigate url="..."
  2. browser_type ref="..." text="..."
  3. browser_click ref="..."
  4. browser_snapshot → [实际看到的内容]
- **预期**: [应该怎样]
- **实际**: [实际怎样]
- **根因**: [代码层面分析]
- **修复状态**: 已修复(commit_hash) / 待修复 / 已知问题
```

---

## 第五部分：与 CI/CD 和任务系统集成

### 5.1 tasks.json 步骤编写规范

在 AI Agent 任务系统（如 claude-coder 的 tasks.json）中编写测试步骤时：

**规则**:
- 每个步骤必须指明使用哪个 Playwright MCP 工具
- 必须包含预期结果描述
- 必须包含失败时的处理方式
- 引用本文档作为测试规范来源

**模板**:
```json
{
  "id": "feat-xxx",
  "description": "[功能] 端到端测试",
  "steps": [
    "阅读 .claude-coder/playwright-testing-guide.md 了解测试规范",
    "前置检查：curl [后端URL]/health 确认后端正常",
    "前置检查：curl [前端URL] 确认前端正常",
    "Phase 1 功能验证：按 playwright-testing-guide.md 2.1 节模板执行核心流程测试",
    "Phase 2 错误场景：按 playwright-testing-guide.md 2.2 节清单测试异常情况",
    "Phase 3 探索性测试：按 playwright-testing-guide.md 2.3 节以 [角色] 身份自由使用系统",
    "将测试结果写入 record/e2e_test_results.md（格式见 playwright-testing-guide.md 第四部分）",
    "对发现的 P0/P1 问题立即修复代码，用 Playwright MCP 复测确认",
    "验证：record/e2e_test_results.md 中功能验证全部 PASS"
  ]
}
```

### 5.2 Playwright MCP 配置模板

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--isolated",
        "--storage-state=path/to/auth.json"
      ]
    }
  }
}
```

> **注意**: `--storage-state` 必须与 `--isolated` 配合使用。没有 `--isolated` 时，Playwright MCP 使用持久化 Chrome Profile，会忽略 `--storage-state` 文件，导致 localStorage 和 cookies 不会被注入。

**可选增强配置**:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--isolated",
        "--storage-state=path/to/auth.json",
        "--save-trace",
        "--save-video=1280x720",
        "--output-dir=test-artifacts",
        "--console-level=warning"
      ]
    }
  }
}
```

### 5.3 storageState 文件模板

```json
{
  "cookies": [
    {
      "name": "session_id",
      "value": "your_session_value",
      "domain": "localhost",
      "path": "/",
      "httpOnly": true,
      "secure": false,
      "sameSite": "Lax"
    }
  ],
  "origins": [
    {
      "origin": "http://localhost:3000",
      "localStorage": [
        {
          "name": "auth_token",
          "value": "your_token_here"
        },
        {
          "name": "user_config",
          "value": "{\"key\":\"value\"}"
        }
      ]
    }
  ]
}
```

---

## 第六部分：Playwright CLI — Token 高效替代方案

> **重要**: 本章节介绍 `@playwright/cli`，一个专为 AI Agent 设计的 token 高效浏览器自动化工具。
> 当测试步骤较多（>5 步）或 token 预算紧张时，应优先考虑 CLI 替代 MCP。

### 6.1 MCP vs CLI 核心对比

| 维度 | Playwright MCP | Playwright CLI |
|------|---------------|----------------|
| **每测试 token 消耗** | ~114,000 | ~27,000 |
| **效率比** | 1x | **4x** |
| **Snapshot 数据** | 注入上下文（50-500KB） | 存磁盘为 YAML 文件 |
| **工具加载** | 26+ 工具完整 JSON schema | `--help` 按需发现 |
| **操作响应** | 结构化元数据 + 更新后的 snapshot | 单行确认信息 |
| **安装方式** | `npx @playwright/mcp@latest` | `npm i -g @playwright/cli@latest` |
| **与 Claude Code 集成** | MCP Server（.mcp.json） | Shell 命令 / Skills |

### 6.2 CLI 安装与基本使用

```bash
# 安装
npm install -g @playwright/cli@latest
playwright-cli install --skills

# 基本流程
playwright-cli open http://localhost:3000/upload     # 打开页面
playwright-cli snapshot                               # 快照存 YAML
playwright-cli fill e15 "测试内容"                     # 填写（用 ref）
playwright-cli click e22                              # 点击
playwright-cli snapshot                               # 再次快照
```

### 6.3 CLI 核心命令速查

| 类别 | 命令 | 说明 |
|------|------|------|
| **导航** | `open`, `goto`, `go-back`, `go-forward`, `reload` | URL 导航 |
| **交互** | `click`, `type`, `fill`, `check`, `drag`, `hover`, `select` | 元素操作 |
| **快照** | `snapshot` | YAML 格式存磁盘，返回元素 ref |
| **截图** | `screenshot`, `pdf` | 视觉验证 |
| **键鼠** | `press`, `keydown`, `mousemove`, `mousewheel` | 底层操作 |
| **存储** | Cookie/localStorage/sessionStorage 管理 | 凭证注入 |
| **会话** | `session-list`, `session-stop`, `session-delete` | 多会话管理 |
| **调试** | `console`, `network`, `tracing-start` | 开发者工具 |

### 6.4 CLI 的 Skills 机制

CLI 将命令暴露为 **Skills**（结构化程序手册），AI Agent 可以：
- 通过 `playwright-cli --help` 发现可用命令（不预加载 schema）
- 通过 `playwright-cli snapshot` 获取页面 YAML 文件路径（不注入上下文）
- 按需读取 YAML 文件中的元素 ref（仅在需要时消耗 token）

### 6.5 Token 节省原理

**MCP 每步的上下文膨胀**:
```
Step 1: navigate → 返回 accessibility tree (8K tokens)
Step 2: fill     → 返回 updated tree (8K tokens)
Step 3: click    → 返回 updated tree (8K tokens)
...
Step 10: snapshot → 返回 tree (8K tokens)
累计: ~80K tokens 仅在 snapshot 数据上
```

**CLI 每步的上下文精简**:
```
Step 1: open url   → "Page opened: http://..." (50 tokens)
Step 2: snapshot   → "Saved to /tmp/pw-snapshot-1.yaml" (30 tokens)
Step 3: fill e15   → "Filled element e15" (20 tokens)
Step 4: click e22  → "Clicked element e22" (20 tokens)
...
Step 10: snapshot  → "Saved to /tmp/pw-snapshot-2.yaml" (30 tokens)
累计: ~200 tokens (仅当 Agent 读取 YAML 时才增加)
```

### 6.6 工具选型决策矩阵

```
你的测试场景是什么？

1. 首次搭建/调试测试 → 用 MCP（交互式、反馈丰富）
2. 步骤 <5 的短测试 → 用 MCP（差异不大，设置简单）
3. 步骤 ≥5 的长流程 → 用 CLI（4x 节省）
4. 多场景回归测试 → 用 CLI（总量大，必须节省）
5. 需要视觉验证 → 用 MCP --caps=vision
6. 探索性测试 → 用 CLI（步骤不可预测，可能很多）
7. CI/CD 自动化 → 用 Playwright Test Runner（npx playwright test）
```

### 6.7 混合工作流示例

```
Phase 1 — 开发期（MCP）:
  用 MCP 交互式调试，建立测试 baseline
  将通过的测试步骤记录到 test-seed.md

Phase 2 — 回归期（CLI）:
  用 CLI 批量执行 test-seed.md 中的场景
  仅在失败时切回 MCP 做精确定位

Phase 3 — CI/CD（Playwright Test）:
  将验证过的流程转为 .test.ts 文件
  用 npx playwright test 在 CI 中执行
  零 AI token 消耗
```

---

## 第七部分：成本优化最佳实践汇总

### 7.1 立即可做的优化（预计节省 40-70%）

| # | 优化措施 | 预计节省 | 实施难度 |
|---|---------|---------|---------|
| 1 | 合并操作后再 snapshot（Smart Snapshot） | 40-60% | 低 |
| 2 | 长流程用 CLI 替代 MCP | 75% | 中 |
| 3 | 使用 `browser_wait_for` 替代轮询 snapshot | 60-80% | 低 |
| 4 | 跳过已缓存通过的测试场景 | 100%（跳过部分） | 中 |
| 5 | 分层测试，非必要不跑 Full E2E | 50%+ | 低 |

### 7.2 高级优化（需要架构调整）

| # | 优化措施 | 预计节省 | 实施难度 |
|---|---------|---------|---------|
| 1 | Trace-first 离线分析（AgentAssay 思想） | 78-100% | 高 |
| 2 | 将 Playwright MCP 测试转为 .test.ts 脚本 | 100%（CI 阶段） | 中 |
| 3 | 使用后端 API 直接验证替代部分浏览器测试 | 80%+ | 中 |
| 4 | 模型降级：Smoke 用 fast model，Full E2E 用 standard | 30-50% | 低 |

### 7.3 相关文档索引

| 文档 | 用途 | 位置 |
|------|------|------|
| Token 预算控制规则 | Session 预算、分层策略、铁律 | `.claude-coder/token-budget-rules.md` |
| 高效测试策略 | Smart Snapshot、优先级排序、缓存 | `.claude-coder/efficient-testing-strategy.md` |
| 测试行为规范 | 元素定位、等待策略、报告格式 | `.claude-coder/testing-rules.md` |
| 测试场景模板 | 可执行的 Playwright 动作序列 | `.claude-coder/test-seed.md` |
| Claude Code 测试规则 | 模块化规则、自动加载 | `.claude/rules/testing.md` |
| 项目配置 | 技术栈、命令、关键路径 | `.claude/CLAUDE.md` |
