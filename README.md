# AI 教学 PPT 生成器

> **Built with [Claude Coder](https://github.com/lk19940215/claude-coder)** — 18 个功能，3 天，由 AI Agent 自主完成 15 个。

教师上传教材内容（拍照 / PDF / 文字），AI 自动生成互动性强、美观的教学 PPT（.pptx），支持 WPS 二次编辑。

## 功能特点

- **多种输入方式**：拍照识别（OCR）、PDF 电子书解析、直接粘贴文字
- **智能内容生成**：AI 根据年级和学科自动调整内容深度和表达方式
- **年级自适应**：小学趣味化、初中体系化，字号配色自动适配
- **英语学科增强**：单词卡、语法图解、情景对话等专属页面类型
- **Canvas 真实预览**：使用 Canvas 2D 渲染 PPT 页面，支持文本/图片/表格/形状的实时预览
- **智能合并编辑**：双 PPT 并排预览，页面级提示语编辑，智能合并生成
- **标准格式输出**：生成 .pptx 文件，WPS / PowerPoint 均可打开编辑
- **多 AI 模型**：支持 DeepSeek / OpenAI / Claude / 智谱 GLM 切换
- **Docker 部署**：前后端容器化，一键启动

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui |
| 后端 | Python FastAPI + SQLite |
| OCR | PaddleOCR |
| PPT 生成 | python-pptx + OOXML |
| Canvas 预览 | 原生 Canvas 2D + LRU 缓存 + 虚拟滚动 |
| 测试 | Playwright E2E |
| 部署 | Docker + docker-compose |

## 开发方式：Claude Coder 自动编码

本项目使用 [Claude Coder](https://github.com/lk19940215/claude-coder)（`npm install -g claude-coder`）进行自主编码开发。

```bash
# 安装
npm install -g @anthropic-ai/claude-agent-sdk
npm install -g claude-coder

# 配置模型
claude-coder setup

# 自动编码（从 requirements.md 驱动）
claude-coder run

# 查看进度
claude-coder status
```

**开发数据**：

| 指标 | 数值 |
|---|---|
| 开发时间 | 3 天（2026.03.02 ~ 03.04） |
| 总功能数 | 18 |
| AI 完成 | 15（83%） |
| 源代码 | 5,729 行（Python 3,700 + TypeScript 2,029） |
| Git commits | 47 |
| E2E 测试 | Playwright 13 用例，10 通过 |

## 快速开始

### 环境要求

| 依赖 | 版本 | 说明 |
|---|---|---|
| Python | 3.11+ | 后端服务 |
| Node.js | 20+ | 前端服务 |
| pnpm | latest | 前端包管理 |
| Git | 2.x+ | 版本控制 |
| Docker | 可选 | 容器化部署 |

### 开发环境启动

```bash
git clone https://github.com/lk19940215/ai-teaching-ppt.git
cd ai-teaching-ppt

# 后端
cd backend && python -m venv ../.venv && source ../.venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd ../frontend && pnpm install && pnpm dev
```

- 前端：http://localhost:3000
- 后端 API 文档：http://localhost:8000/docs

## Canvas 预览功能

### 功能概述

Canvas 预览功能（`/merge` 页面）允许用户上传两个 PPTX 文件，通过真实的 Canvas 渲染预览页面内容，然后通过页面级提示语编辑，智能合并生成新的 PPT。

### 支持的渲染格式

| 格式 | 支持程度 | 说明 |
|---|---|---|
| 文本 | ✅ 完全支持 | 支持字体、大小、颜色、粗体、斜体、下划线、对齐 |
| 图片 | ✅ 完全支持 | Base64 格式，自动压缩优化 |
| 表格 | ✅ 完全支持 | 表格边框、单元格内容渲染 |
| 形状 | ✅ 支持 | 矩形、圆形等基础形状 |
| 动画 | ❌ 不支持 | Canvas 静态渲染，动画在生成的 PPTX 中保留 |

### Canvas 预览 vs CSS 预览

| 特性 | Canvas 预览 | CSS 预览（旧） |
|---|---|---|
| 渲染方式 | Canvas 2D 真实绘制 | CSS 样式模拟 |
| 文本样式 | 完整支持（字体/颜色/大小） | 部分支持 |
| 图片渲染 | 真实显示 | 占位符 |
| 表格渲染 | 真实表格 | 简化列表 |
| 性能 | 离屏缓存 + 虚拟滚动 | 轻量但功能有限 |
| 适用场景 | PPT 智能合并 | 简单预览 |

### 性能优化策略

Canvas 预览组件采用了多种性能优化策略，确保大量页面渲染时的流畅体验：

| 优化技术 | 说明 | 效果 |
|---|---|---|
| **离屏 Canvas 缓存** | LRU 缓存已渲染页面，避免重复渲染 | 缓存命中率>80% |
| **requestIdleCallback** | 利用浏览器空闲时间分片渲染 | 不阻塞主线程 |
| **虚拟滚动** | 只渲染可视区域内的缩略图 | 50 页以上自动启用 |
| **懒加载** | 按页面索引延迟渲染（前 20 页优先） | 初始渲染时间<1s |
| **简化渲染模式** | 缩略图模式只绘制标题和色块 | 单页渲染时间<50ms |
| **内存监控** | Canvas 尺寸超限自动降级 | 防止内存溢出 |

### 降级机制

当 Canvas 渲染失败时（浏览器不支持、内存不足、格式不兼容），系统会自动切换到降级模式：

1. **后端解析降级**：调用 `/api/v1/ppt/parse` 获取简化版文本数据
2. **CSS 降级渲染**：使用 CSS 样式显示文本内容
3. **错误提示**：显示降级原因和重试按钮

降级模式支持以下错误场景：
- 浏览器不支持 Canvas 2D
- Canvas 尺寸过大导致内存不足
- 渲染超时（>5 秒）
- 特殊格式无法解析

### 兼容性

| 浏览器 | 支持情况 | 备注 |
|---|---|---|
| Chrome 90+ | ✅ 完全支持 | 推荐浏览器 |
| Firefox 88+ | ✅ 完全支持 | |
| Safari 14+ | ✅ 支持 | 部分性能优化降级 |
| Edge 90+ | ✅ 完全支持 | Chromium 内核 |

### 使用指南

1. 访问 `/merge` 页面
2. 上传两个 PPTX 文件
3. 等待 Canvas 渲染完成（显示缩略图预览）
4. 点击选择需要合并的页面（支持 Shift/Ctrl 多选）
5. 在右侧提示语面板编辑页面级提示语
6. 点击"开始智能合并"，等待 SSE 进度完成
7. 下载合并后的 PPTX 文件

### Docker 部署

```bash
docker-compose up -d
```

## 项目结构

```
ai-teaching-ppt/
├── backend/           # Python FastAPI 后端
│   ├── app/
│   │   ├── api/       # API 路由
│   │   ├── services/  # 业务逻辑（OCR、PPT生成、LLM）
│   │   └── models/    # 数据模型
├── frontend/          # Next.js 14 前端
│   ├── app/           # 页面路由
│   └── components/    # UI 组件
├── tests/             # Playwright E2E 测试
├── .claude-coder/     # Claude Coder 运行时数据
└── requirements.md    # 需求文档
```

## License

MIT


```
claude --auto-accept-edits --allowed-tools edit,read,write,grep
```