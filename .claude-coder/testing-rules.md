# AI Agent 自动化测试通用规则

> 本文档是 AI Agent（Claude/Opus/GPT）执行端到端测试的行为规范。
> 当 tasks.json 中的任务包含测试步骤时，Agent 必须遵循本文档规则。

---

## 一、核心原则

### 1. 必须真实操作，禁止替代验证

| 允许 | 禁止 |
|------|------|
| Playwright MCP browser_navigate 访问页面 | curl 访问页面然后说"通过" |
| browser_fill 在文本框输入内容 | 读代码说"文本框存在" |
| browser_click 点击按钮并等待结果 | 看代码说"按钮逻辑正确" |
| browser_snapshot 截图验证状态 | 假设页面状态正常 |

**铁律：代码审查不等于测试。测试必须产生浏览器交互。**

### 2. 测试业务需求，而非代码实现

- 测试应验证"用户能否完成任务"，而非"代码是否存在某个函数"
- 断言应基于用户可见的结果（页面文本、按钮状态、下载文件），而非内部变量
- 示例：不要断言 `setGeneratedContent` 被调用，要断言页面出现"PPT 预览"区域

### 3. 测试必须独立且可重复

- 每个测试场景不依赖其他测试的执行结果
- 测试前清理状态（如需要），测试后记录结果
- 不修改 playwright-auth.json 中的凭证

### 4. 发现问题时先调查，再修复

- 测试失败时，不要立即修改测试让它通过
- 先分析：是产品 bug？还是测试写错了？还是环境问题？
- 记录根因分析到测试报告中

---

## 二、Playwright MCP 测试工具使用规范

### 可用工具清单

| 工具 | 用途 | 使用时机 |
|------|------|----------|
| `browser_navigate` | 导航到 URL | 每个测试开始时 |
| `browser_snapshot` | 获取页面可访问性快照 | 每个操作后验证状态 |
| `browser_click` | 点击元素（用 ref 或文本） | 按钮、链接、选项卡 |
| `browser_fill` | 填写输入框 | 文本框、搜索框 |
| `browser_select` | 选择下拉选项 | 年级、学科等选择器 |
| `browser_console_messages` | 检查控制台消息 | 验证无错误 |
| `browser_upload_file` | 上传文件 | 图片/PDF 上传测试 |
| `browser_wait` | 等待条件满足 | 异步操作完成后 |

### 元素定位优先级

1. **ARIA role + name**（最佳）: `getByRole('button', { name: '生成教学 PPT' })`
2. **文本内容**: `getByText('PPT 预览')`
3. **ref 属性**: `ref="E12"`（从 snapshot 中获取）
4. **CSS 选择器**（最后手段）: 避免使用

### 等待策略

- 短操作（页面导航、按钮点击）：操作后立即 `browser_snapshot`
- 中等操作（表单提交、API 调用）：等待 5-10 秒后 `browser_snapshot`
- 长操作（PPT 生成，涉及 LLM 调用）：**每 10 秒 `browser_snapshot` 一次，最多等 180 秒**
- 超时判定：超过最大等待时间且页面无变化 = 失败

---

## 三、测试场景设计模板

### A. 功能验证测试（Happy Path）

```
场景：[功能名称]
前置条件：[需要什么状态/数据]
步骤：
  1. browser_navigate → [URL]
  2. browser_snapshot → 确认 [预期元素] 可见
  3. browser_fill → 在 [输入框] 输入 [测试数据]
  4. browser_click → 点击 [按钮]
  5. 等待 → [等待策略]
  6. browser_snapshot → 验证 [预期结果]
预期结果：[用户可见的成功标志]
失败标志：[什么情况算失败]
```

### B. 错误场景测试（Unhappy Path）

```
场景：[错误场景名称]
步骤：
  1. [触发错误条件的操作]
  2. browser_snapshot → 验证 [错误提示文案]
预期结果：[友好的错误提示，非空白页或 500 错误]
```

### C. 探索性测试（AI 自主发现）

```
角色：你是一位 [目标用户角色]，第一次使用这个系统
任务：完成 [具体业务目标]
规则：
  - 像真实用户一样操作，不要跳步
  - 遇到困惑或受阻时，记录下来
  - 记录每个"不符合直觉"的交互
  - 记录每个"等待时间过长"的操作
输出：将发现的问题写入 record/[报告文件名].md
```

---

## 四、测试数据规范

### 文本内容（至少 100 字，覆盖学科特征）

**数学测试文本：**
```
三角形的面积等于底乘以高除以二。常见的三角形类型包括等边三角形、
等腰三角形和直角三角形。在直角三角形中，两条直角边可以作为底和
高。例如：一个底为6厘米、高为4厘米的三角形，面积为6×4÷2=12
平方厘米。求解三角形面积时，关键是找到对应的底和高。
```

**英语测试文本：**
```
Unit 5: My Family. Key vocabulary: father, mother, brother, sister, 
grandfather, grandmother. Key sentences: This is my father. He is a 
teacher. She is my mother. She is a doctor. How many people are there 
in your family? There are five people in my family.
```

**语文测试文本：**
```
《静夜思》唐·李白。床前明月光，疑是地上霜。举头望明月，低头思
故乡。这首诗表达了诗人在寂静的夜晚，看到明亮的月光，引发了对
故乡的思念之情。"疑是地上霜"运用了比喻的修辞手法。
```

### 配置参数组合

| 场景 | 年级 | 学科 | 风格 | 页数 |
|------|------|------|------|------|
| 低年级数学 | 小学三年级 | 数学 | 活泼趣味 | 12 |
| 初中英语 | 初中二年级 | 英语 | 学科主题 | 15 |
| 高中语文 | 高中一年级 | 语文 | 简约清晰 | 20 |

---

## 五、测试报告格式

每次测试完成后，输出报告到 `record/` 目录，格式如下：

```markdown
# [测试名称] 测试报告

**测试时间**: YYYY-MM-DD HH:MM
**测试工具**: Playwright MCP
**测试环境**: 前端 localhost:3000 / 后端 localhost:8000

## 测试结果摘要

| 场景 | 结果 | 耗时 | 备注 |
|------|------|------|------|
| [场景1] | 通过/失败 | Xs | [简要说明] |

## 详细记录

### 场景 1: [名称]

**步骤**:
1. [实际执行的操作]
2. [观察到的结果]

**截图/快照**: [browser_snapshot 的关键内容]

**结论**: 通过/失败

## 发现的问题

### 问题 1: [标题]
- **严重程度**: 高/中/低
- **复现步骤**: [1, 2, 3...]
- **预期行为**: [应该怎样]
- **实际行为**: [实际怎样]
- **根因分析**: [代码层面的原因]
- **建议修复**: [修复方案]
```

---

## 六、与 tasks.json 的集成规范

当在 tasks.json 中编写测试任务时，步骤必须遵循以下格式：

### 步骤编写规则

1. **每个步骤必须对应一个 Playwright MCP 动作**
2. **步骤中必须包含预期结果**
3. **必须包含失败时的处理指令**

### 示例

```json
{
  "steps": [
    "前置：确认前后端服务运行中（curl http://localhost:8000/health 和 curl http://localhost:3000）",
    "使用 Playwright MCP browser_navigate 访问 http://localhost:3000/upload",
    "使用 browser_snapshot 确认页面包含'上传教材内容'标题",
    "使用 browser_fill 在文本输入框填入数学测试内容（见 .claude-coder/testing-rules.md 测试数据）",
    "使用 browser_select 选择年级=小学三年级、学科=数学、风格=活泼趣味",
    "使用 browser_click 点击'生成教学 PPT'按钮",
    "每 10 秒执行 browser_snapshot，最多等待 180 秒，观察进度变化",
    "验证成功：页面出现'PPT 预览'区域且包含可翻页的缩略图",
    "验证失败：页面出现红色错误提示 → 记录错误文案到 record/e2e_test_results.md",
    "成功后：使用 browser_click 点击'下载 PPT'，确认触发文件下载"
  ]
}
```

---

## 七、凭证与认证

### localStorage 预置

`.claude-coder/playwright-auth.json` 已配置 `llm_config`，包含有效的 API Key。
Playwright MCP 通过 `--storage-state` 参数自动注入。

### 验证凭证是否生效

测试开始时，执行以下检查：
1. `browser_navigate` 到 `/upload`
2. `browser_snapshot` 查看页面
3. 如果页面显示"请先在设置页面配置 LLM API Key"错误 = 凭证未注入
4. 如果可以正常点击生成 = 凭证已生效

### 凭证失效处理

如果凭证过期或无效：
1. 不要修改 playwright-auth.json
2. 在测试报告中标注"凭证失效"
3. 提示用户运行 `claude-coder auth localhost:3000` 更新凭证
