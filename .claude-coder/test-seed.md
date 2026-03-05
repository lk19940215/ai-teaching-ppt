# Playwright MCP 测试种子文件

> 本文件是 AI Agent 执行端到端测试的操作手册。
> 每个测试场景都是一个完整的、可直接执行的 Playwright MCP 动作序列。
> Agent 必须按顺序执行每个步骤，不得跳过或用代码审查替代。

---

## 前置检查

在执行任何测试前，先完成环境检查：

```
步骤 1: 执行 curl -s http://localhost:8000/health
  - 预期: 返回 {"status": "healthy"}
  - 失败: 后端未启动，执行 cd backend && uvicorn app.main:app --reload --port 8000

步骤 2: 执行 curl -s http://localhost:3000 | head -c 100
  - 预期: 返回 HTML 内容
  - 失败: 前端未启动，执行 cd frontend && pnpm dev

步骤 3: browser_navigate → http://localhost:3000/upload
步骤 4: browser_snapshot → 检查页面是否包含"上传教材内容"
  - 如果页面空白或报错: 服务异常，停止测试
  - 如果正常: 继续
```

---

## 场景 A: 文字输入 → 生成数学 PPT（完整流程）

**目标**: 验证核心生成流程端到端可用

```
步骤 A1: browser_navigate → http://localhost:3000/upload
步骤 A2: browser_snapshot → 确认页面加载，找到文本输入框的 ref

步骤 A3: browser_fill → 在文本输入框输入以下内容：
  "三角形的面积等于底乘以高除以二。常见的三角形类型包括等边三角形、等腰三角形和直角三角形。在直角三角形中，两条直角边可以作为底和高。例如：一个底为6厘米、高为4厘米的三角形，面积为6×4÷2=12平方厘米。求解三角形面积时，关键是找到对应的底和高。注意：底和高必须是对应的，即高是底边上的高。"

步骤 A4: browser_snapshot → 确认文本已填入，生成按钮不是 disabled 状态

步骤 A5: browser_select → 年级选择"小学五年级"
步骤 A6: browser_select → 学科选择"数学"  
步骤 A7: browser_select → 风格选择"活泼趣味（适合低年级）"

步骤 A8: browser_snapshot → 确认所有参数已选择

步骤 A9: browser_click → 点击"生成教学 PPT"按钮

步骤 A10: 等待循环（最关键的步骤）
  - 每 10 秒执行一次 browser_snapshot
  - 观察页面变化：
    a. 出现进度条/加载动画 → 正常，继续等待
    b. 出现"PPT 预览"区域 → 生成成功，跳到 A11
    c. 出现红色错误提示 → 生成失败，记录错误文案，跳到 A_FAIL
    d. 180 秒内无任何变化 → 超时，跳到 A_FAIL
  - 同时执行 browser_console_messages → 检查有无 JS 错误

步骤 A11（成功）: browser_snapshot → 验证以下元素存在：
  - "PPT 预览" 或 "生成结果" 标题
  - 可翻页的缩略图区域
  - "下载 PPT" 按钮
  - 页码显示（如 "1 / 15"）

步骤 A12: browser_click → 点击"下载 PPT"按钮
步骤 A13: 验证下载 URL 有效：curl -sI [下载URL] | grep "200 OK"

步骤 A_FAIL（失败处理）:
  - browser_snapshot → 截取当前页面完整状态
  - browser_console_messages → 获取所有控制台消息
  - 将以下信息记录到 record/e2e_test_results.md：
    * 失败时间
    * 失败步骤编号
    * 错误文案或截图内容
    * 控制台错误信息
    * 分析可能的原因
```

---

## 场景 B: 英语学科 PPT 生成

**目标**: 验证英语学科专属提示词和页面类型

```
步骤 B1: browser_navigate → http://localhost:3000/upload
步骤 B2: browser_fill → 输入英语教学内容：
  "Unit 5: My Family. Key vocabulary: father, mother, brother, sister, grandfather, grandmother. Key sentences: This is my father. He is a teacher. She is my mother. She is a doctor. How many people are there in your family? There are five people in my family. Grammar focus: This is / These are / How many"

步骤 B3: browser_select → 年级="初中一年级"，学科="英语"，风格="学科主题"
步骤 B4: browser_click → 点击生成按钮
步骤 B5: 等待循环（同场景 A 步骤 A10）
步骤 B6: 验证成功后，检查预览内容中是否包含英语学科特色：
  - 单词学习页（vocabulary）
  - 语法讲解页（grammar）
  - 情景对话页（dialogue）
步骤 B7: 下载并记录结果
```

---

## 场景 C: 错误场景测试

### C1: 无内容时按钮应该禁用

```
步骤 C1-1: browser_navigate → http://localhost:3000/upload
步骤 C1-2: browser_snapshot → 检查"生成教学 PPT"按钮
  - 预期：按钮是 disabled 状态（文本框为空时）
  - 如果按钮可点击：记录为 BUG
```

### C2: 清除 API Key 后应该提示错误

```
步骤 C2-1: browser_navigate → http://localhost:3000/upload
步骤 C2-2: browser_evaluate → localStorage.removeItem('llm_config')
步骤 C2-3: browser_navigate → http://localhost:3000/upload（刷新页面）
步骤 C2-4: browser_fill → 输入任意文本内容
步骤 C2-5: browser_click → 点击生成按钮
步骤 C2-6: browser_snapshot → 验证页面显示 API Key 相关错误提示
  - 预期："请先在设置页面配置 LLM API Key" 或类似提示
  - 如果无提示或直接报错：记录为 BUG
步骤 C2-7: 恢复 → browser_navigate → http://localhost:3000/upload
  （storageState 会在下次导航时重新注入 localStorage）
```

### C3: 无效 API Key 应该返回友好错误

```
步骤 C3-1: browser_navigate → http://localhost:3000/settings
步骤 C3-2: browser_fill → API Key 输入 "sk-invalid-test-key-12345"
步骤 C3-3: browser_click → 点击"测试连接"按钮
步骤 C3-4: browser_snapshot → 验证显示连接失败的友好提示
  - 预期：显示"连接失败"或"API Key 无效"等提示
  - 如果无响应或显示技术错误栈：记录为 BUG
```

---

## 场景 D: 历史记录验证

**前置**: 需要先执行场景 A 成功生成一次 PPT

```
步骤 D1: browser_navigate → http://localhost:3000/history
步骤 D2: browser_snapshot → 检查页面内容
  - 如果有生成记录：验证记录包含主题、年级、学科、时间信息
  - 如果显示"暂无历史记录"：可能是 session_id 不一致，记录为已知问题
步骤 D3: 如果有记录，尝试点击"重新下载"按钮
步骤 D4: browser_snapshot → 验证下载是否触发
```

---

## 场景 E: 探索性测试（AI 自主发现问题）

**指令**: 你是一位小学数学教师，第一次使用 AI 教学 PPT 生成器。

```
任务 1: 从首页开始，找到生成 PPT 的入口，为你的"分数加减法"课程生成一份 PPT
任务 2: 生成完成后，预览 PPT 内容，检查是否符合小学五年级的教学要求
任务 3: 下载 PPT 文件
任务 4: 去历史记录页面查看是否有记录
任务 5: 去设置页面查看当前的 AI 模型配置

在整个过程中记录：
- 每一步的等待时间（是否过长？）
- 每一个不清楚的按钮或提示
- 每一个让你困惑的交互
- 每一个看起来不对的样式或布局
- 生成的 PPT 内容是否真的对教学有帮助

将所有发现写入 record/exploratory_test.md
```

---

## 测试结果输出模板

每次测试完成后，将结果写入 `record/e2e_test_results.md`：

```markdown
# E2E 测试结果

**日期**: [YYYY-MM-DD]
**工具**: Playwright MCP
**凭证**: playwright-auth.json (storageState)

## 结果摘要

| 场景 | 结果 | 耗时 | 关键发现 |
|------|------|------|----------|
| A: 数学PPT生成 | 通过/失败 | XXs | |
| B: 英语PPT生成 | 通过/失败 | XXs | |
| C1: 空内容禁用 | 通过/失败 | - | |
| C2: 无API Key | 通过/失败 | - | |
| C3: 无效Key | 通过/失败 | - | |
| D: 历史记录 | 通过/失败 | - | |
| E: 探索性测试 | [发现N个问题] | - | |

## 发现的问题

（按 testing-rules.md 中的问题格式记录）
```
