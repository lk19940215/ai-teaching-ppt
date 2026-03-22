# AI Teaching PPT

## WHAT（做什么）

一个基于 Web 的 PPT 处理工具：用户上传 PPTX 文件，系统解析内容在浏览器中展示，用户选择页面进行 AI 润色/改写/扩展/提取，最终导出保留原始格式的 PPTX 文件。

## WHY（为什么做）

帮助教师和内容创作者快速优化 PPT 内容，无需手动逐页编辑。AI 处理保持原有格式（字体、颜色、动画），只修改文字内容。

## HOW（怎么做）

### 技术架构

```
Frontend (Next.js 15)     Backend (FastAPI)      AI (OpenAI 兼容 API)
     │                         │                        │
     │   1. 上传 PPTX          │                        │
     ├────────────────────────►│                        │
     │                         │   2. PPTXReader 解析   │
     │   3. 返回结构化数据      │                        │
     │◄────────────────────────┤                        │
     │                         │                        │
     │   4. 选择页面+AI操作     │                        │
     ├────────────────────────►│   5. 调用 LLM          │
     │                         ├───────────────────────►│
     │                         │   6. 返回修改指令       │
     │   7. 返回修改预览        │◄───────────────────────┤
     │◄────────────────────────┤                        │
     │                         │                        │
     │   8. 确认修改            │                        │
     ├────────────────────────►│   9. PPTXWriter 写回   │
     │   10. 下载链接          │                        │
     │◄────────────────────────┤                        │
```

### 核心模块

| 模块 | 路径 | 职责 |
|------|------|------|
| PPTXReader | backend/app/core/pptx_reader.py | 解析 PPTX 为结构化 JSON |
| ContentExtractor | backend/app/core/content_extractor.py | 提取 AI 友好文本 |
| AIProcessor | backend/app/ai/processor.py | LLM 处理编排 |
| PPTXWriter | backend/app/core/pptx_writer.py | Run 级别写回，保留格式 |

### API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| /api/v1/ppt/upload | POST | 上传 PPTX，返回解析结果 |
| /api/v1/ppt/process | POST | AI 处理选定页面 |
| /api/v1/ppt/apply | POST | 确认修改，生成新 PPTX |
| /api/v1/ppt/download/{session_id} | GET | 下载生成的文件 |
| /api/v1/config/llm | GET/POST | 获取/保存 LLM 配置 |

### 启动命令

```bash
# 后端（端口 9501）
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 9501 --reload

# 前端（端口 3000）
cd frontend && pnpm dev
```

### 数据模型（三层管道）

1. **PPTX 解析模型** (ParsedPresentation)：完整表示 PPTX 结构
2. **AI 友好内容模型** (SlideContent)：纯文本 + 源映射
3. **修改指令模型** (ProcessingResult)：精确描述改什么、改成什么

详细定义见 docs/technical-spec.md。

### 关键技术点

- **Run 级别文本替换**：只修改 <a:t> 节点，保留 <a:rPr> 格式属性
- **shape_index 映射**：通过索引定位原始 Shape 进行修改
- **OpenAI 兼容协议**：支持 DeepSeek、GLM、Claude 等多家模型

### 项目状态

当前处于重构阶段，详见 docs/refactor-plan.md。
