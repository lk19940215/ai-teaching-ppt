# 需求文档 / Requirements

> 将本文件复制为 `requirements.md`，填写你的需求后启动：
> ```bash
> cp requirements.example.md requirements.md
> vim requirements.md   # 编辑你的需求
> claude-coder run
> ```
> Agent 会在初始化和每个 session 中自动读取此文件。
> **你可以随时修改 `requirements.md`**：新增的功能需求会在下次 session 中自动同步到 `tasks.json`；发现需要改进的地方，补充到下方功能需求或「其他要求」即可。

---

## 项目概述（必填）

<!-- 一两句话描述你要做什么 -->

例如：做一个网页版的 AI 文章总结工具，用户粘贴 URL 后自动抓取内容并生成摘要。

## 功能需求（必填）

<!-- 列出你需要的功能，越具体越好 -->

- [ ] 功能 1：用户输入 URL，后端抓取文章内容
- [ ] 功能 2：调用 LLM API 生成中文摘要
- [ ] 功能 3：前端展示摘要结果，支持复制
- [ ] 功能 4：历史记录，保存已总结的文章
- [ ] 功能 5：...

## 技术约束（可选）

<!-- 如果你对技术栈有偏好，写在这里。不写则由 Agent 自行决定。 -->

- 后端：Python FastAPI
- 前端：React + Vite
- 数据库：SQLite
- 状态管理：Zustand（不要用 Redux）
- LLM：OpenAI API（gpt-4o）

## 样式与设计（可选）

<!-- UI 风格、配色、参考链接等。不写则由 Agent 自行决定。 -->

- 整体风格：简约、现代，参考 Notion
- 配色：深色主题为主，主色调 #4F46E5（靛蓝）
- CSS 框架：Tailwind CSS
- 移动端适配：是
- 参考链接：https://example.com/design-reference

## 其他要求（可选）

<!-- 性能、安全、部署、国际化等任何额外要求 -->

- 支持中英文界面
- API 响应时间 < 3 秒
- 需要 Docker 部署支持
