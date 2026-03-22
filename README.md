# AI Teaching PPT

一个基于 Web 的 PPT 智能处理工具，支持**课文生成 PPT** 和 **PPT 智能合并** 两大核心功能，保留原始格式导出。

---

## 核心功能

### 1. 课文生成 PPT (`/generate`)

**场景**：从课文内容快速生成教学课件

**流程**：
1. 输入课文内容（支持学科、年级标签）
2. AI 自动生成教学大纲（基于 ADDIE 模型）
3. 可编辑调整大纲
4. 生成 PPTX 文件下载

**AI 大纲设计原则**：
- 学习目标 → 课堂导入 → 新知呈现 → 操练巩固 → 拓展应用 → 课堂小结
- 每页 2-5 个要点，语言简洁
- 包含教师备注（教学策略、时间建议）

---

### 2. PPT 智能合并 (`/merge`)

**场景**：对现有 PPT 进行 AI 优化或多 PPT 融合

**流程**：
1. 上传 1-2 个 PPTX 文件（支持 .ppt 自动转换）
2. 选择页面进行 AI 处理
3. 组合生成新 PPT

**AI 处理类型**：

| 操作 | 说明 |
|------|------|
| 润色 | 优化语言表达，修正语法错误 |
| 改写 | 改变表述风格，适配不同场景 |
| 扩展 | 补充相关知识点，丰富内容 |
| 提取 | 提炼核心要点，精简内容 |
| 融合 | 将多个 PPT 页面内容融合为一页 |

**特色功能**：
- **版本管理**：每次处理生成新版本，可回溯对比
- **页面组合**：从不同 PPT 选择页面组合新 PPT
- **格式保留**：字体、颜色、动画等原始格式完整保留

---

## 核心依赖

### 必需依赖

#### 1. LibreOffice（预览图生成）

**作用**：
- **预览图生成**：将 PPTX 每页转换为 PNG 图片用于浏览器预览
  - 转换流程：`PPTX → LibreOffice (headless) → PDF → PyMuPDF → PNG`
- **格式转换**：自动将旧版 `.ppt` 文件转换为 `.pptx`

**安装方式**：

| 平台 | 安装命令/方式 |
|------|--------------|
| **Windows** | 1. 访问 https://www.libreoffice.org/download/download/<br>2. 下载 Windows 版本安装包（约 300MB）<br>3. 运行安装程序，默认安装即可<br>4. 无需配置环境变量，程序会自动检测 |
| **macOS** | `brew install --cask libreoffice` |
| **Ubuntu/Debian** | `sudo apt update && sudo apt install libreoffice` |
| **CentOS/RHEL** | `sudo yum install libreoffice` |
| **Arch Linux** | `sudo pacman -S libreoffice` |

**验证安装**：
```bash
# Linux/macOS
soffice --version
# 或
libreoffice --version

# Windows（在 CMD 或 PowerShell 中）
"C:\Program Files\LibreOffice\program\soffice.exe" --version
```

> **注意**：未安装 LibreOffice 时：
> - 上传功能正常，但无预览图显示
> - `.ppt` 文件无法自动转换，需手动转为 `.pptx` 后上传

---

#### 2. Python 3.9+（后端运行环境）

**作用**：运行 FastAPI 后端服务

**安装方式**：
- **Windows**：从 https://www.python.org/downloads/ 下载安装
- **macOS**：`brew install python@3.11`
- **Linux**：系统通常已预装，或 `sudo apt install python3 python3-pip`

**验证安装**：
```bash
python --version   # 应显示 Python 3.9+
pip --version
```

---

#### 3. Node.js 18+ & pnpm（前端运行环境）

**作用**：运行 Next.js 前端服务

**安装方式**：

| 工具 | 安装方式 |
|------|----------|
| **Node.js** | 从 https://nodejs.org/ 下载 LTS 版本 |
| **pnpm** | `npm install -g pnpm` |

**验证安装**：
```bash
node --version    # 应显示 v18.x 或更高
pnpm --version    # 应显示 8.x 或更高
```

---

### Python 依赖（后端）

位于 `backend/requirements.txt`：

| 依赖包 | 版本 | 用途 |
|--------|------|------|
| `fastapi` | 0.104.1 | Web 框架 |
| `uvicorn[standard]` | 0.24.0 | ASGI 服务器 |
| `python-multipart` | 0.0.6 | 文件上传支持 |
| `pydantic` | 2.5.0 | 数据验证 |
| `pydantic-settings` | 2.1.0 | 配置管理 |
| `sqlalchemy` | 2.0.23 | ORM |
| `python-pptx` | 0.6.23 | **PPTX 读写核心库** |
| `pymupdf` | 1.23.8 | PDF 转图片（预览生成） |
| `openai` | ≥2.24.0 | OpenAI 兼容 API 客户端 |
| `pillow` | - | 图像处理 |
| `python-dotenv` | 1.0.0 | 环境变量加载 |
| `aiofiles` | 23.2.1 | 异步文件操作 |
| `jieba` | ≥0.42.1 | 中文分词 |
| `json5` | ≥0.9.0 | JSON5 解析 |

---

### Node.js 依赖（前端）

位于 `frontend/package.json`：

| 依赖包 | 用途 |
|--------|------|
| `next` | React 框架（App Router） |
| `react` / `react-dom` | UI 库 |
| `tailwindcss` | CSS 框架 |
| `@dnd-kit/core` / `@dnd-kit/sortable` | 拖拽排序 |
| `@radix-ui/*` | UI 组件基础 |
| `axios` | HTTP 客户端 |
| `shadcn-ui` | UI 组件库 |

---

## 安装说明

### 步骤 1：安装 LibreOffice

根据你的操作系统，参考上方「核心依赖」中的安装方式。

### 步骤 2：克隆项目

```bash
git clone https://github.com/your-repo/ai-teaching-ppt.git
cd ai-teaching-ppt
```

### 步骤 3：后端安装与配置

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows (CMD):
.venv\Scripts\activate.bat
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

**配置 LLM（编辑 `.env` 文件）**：

```bash
# 复制示例配置
cp .env.example .env   # 如果没有 .env.example，直接创建 .env
```

`.env` 文件内容：

```env
# LLM 配置（JSON 格式）
# 支持 OpenAI 兼容 API：DeepSeek、GLM、Claude、阿里云等
LLM_CONFIG={"provider":"deepseek","apiKey":"sk-xxx","baseUrl":"https://api.deepseek.com","model":"deepseek-chat","temperature":0.8,"maxInputTokens":8192,"maxOutputTokens":4096}
```

**配置参数说明**：

| 参数 | 说明 | 示例 |
|------|------|------|
| `provider` | 提供商标识 | `deepseek`、`openai`、`glm`、`claude` |
| `apiKey` | API 密钥 | `sk-xxx` |
| `baseUrl` | API 基础地址 | `https://api.deepseek.com` |
| `model` | 模型名称 | `deepseek-chat`、`gpt-4`、`glm-4` |
| `temperature` | 生成温度 (0-1) | `0.8` |
| `maxInputTokens` | 最大输入 token | `8192` |
| `maxOutputTokens` | 最大输出 token | `4096` |

**常用 LLM 配置示例**：

```env
# DeepSeek
LLM_CONFIG={"provider":"deepseek","apiKey":"sk-xxx","baseUrl":"https://api.deepseek.com","model":"deepseek-chat"}

# OpenAI
LLM_CONFIG={"provider":"openai","apiKey":"sk-xxx","baseUrl":"https://api.openai.com/v1","model":"gpt-4o"}

# 智谱 GLM
LLM_CONFIG={"provider":"glm","apiKey":"xxx","baseUrl":"https://open.bigmodel.cn/api/paas/v4","model":"glm-4"}

# 阿里云百炼
LLM_CONFIG={"provider":"aliyun","apiKey":"sk-xxx","baseUrl":"https://dashscope.aliyuncs.com/compatible-mode/v1","model":"qwen-plus"}
```

### 步骤 4：前端安装

```bash
# 进入前端目录
cd ../frontend

# 安装依赖
pnpm install
```

### 步骤 5：启动服务

**启动后端**（终端 1）：

```bash
cd backend
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS
python -m uvicorn app.main:app --host 0.0.0.0 --port 9501 --reload
```

**启动前端**（终端 2）：

```bash
cd frontend
pnpm dev
```

### 步骤 6：访问应用

- **前端界面**：http://localhost:3000
- **后端 API 文档**：http://localhost:9501/docs

---

## 使用说明

### 功能一：课文生成 PPT

**入口**：访问 http://localhost:3000/generate

#### 步骤 1：输入课文内容

1. 填写「学科」（可选）：如「英语」、「数学」
2. 填写「年级」（可选）：如「八年级」、「高一」
3. 在文本框中粘贴课文全文或核心段落（至少 10 个字符）

#### 步骤 2：生成教学大纲

1. 点击「生成教学大纲」按钮
2. 等待 AI 生成（通常 5-15 秒）
3. 生成的大纲包含：
   - 标题页
   - 学习目标
   - 课堂导入
   - 新知呈现（多页）
   - 操练巩固
   - 拓展应用
   - 课堂小结

#### 步骤 3：编辑大纲（可选）

- 修改课件标题
- 编辑任意幻灯片的标题和内容
- 删除不需要的幻灯片
- 添加新的幻灯片

#### 步骤 4：生成并下载 PPT

1. 点击「生成 PPT」按钮
2. 等待生成完成（通常几秒）
3. 点击「下载 PPT」获取文件

#### 后续优化

生成完成后，页面会引导你前往「PPT 智能合并」功能，对生成的 PPT 进行进一步优化。

---

### 功能二：PPT 智能合并

**入口**：访问 http://localhost:3000/merge

#### 步骤 1：上传 PPT 文件

1. 点击上传区域选择文件
2. 支持上传 1-2 个 PPTX 文件
   - 至少上传 1 个文件
   - 上传 2 个文件可进行跨 PPT 融合
3. 支持 `.ppt` 格式（自动转换为 `.pptx`）
4. 文件大小限制：单个文件最大 20MB
5. 上传后自动生成预览图
6. 点击「开始处理」进入编辑界面

#### 步骤 2：选择并处理页面

**浏览幻灯片**：
- 顶部幻灯片池显示所有上传的 PPT 页面
- PPT A / PPT B 分开展示
- 融合结果显示在独立区域

**选择页面**：
- 点击任意幻灯片选中
- 选中后右侧显示大预览图

**AI 处理**：
1. 选中一个或多个页面
2. 在右侧操作面板选择处理类型：
   - **润色**：优化表达，修正错误
   - **改写**：改变风格
   - **扩展**：补充内容
   - **提取**：精简内容
   - **融合**：合并多页内容
3. 可输入自定义提示词
4. 点击执行，等待 AI 处理
5. 处理完成后自动生成新版本

**版本管理**：
- 每次处理生成新版本
- 点击版本标签切换查看
- 可随时回退到任意版本

#### 步骤 3：组合最终 PPT

**添加到最终选择**：
- 点击幻灯片上的「+」按钮添加到最终选择栏
- 或选中后点击「添加到最终选择」按钮

**排序调整**：
- 拖拽最终选择栏中的幻灯片调整顺序
- 点击「×」移除不需要的页面

**生成最终文件**：
1. 确认最终选择栏中的页面顺序
2. 点击「生成最终 PPT」按钮
3. 等待生成完成

#### 步骤 4：下载

1. 生成完成后自动跳转到下载页面
2. 点击「下载 PPT」获取文件
3. 可选择「返回修改」继续编辑
4. 或「重新开始」清空所有内容

---

## API 端点

### PPT 处理 (`/api/v1/ppt`)

| 端点 | 方法 | 功能 |
|------|------|------|
| `/upload` | POST | 上传 PPTX（支持 1-2 个文件） |
| `/process` | POST | AI 处理选定页面 |
| `/compose` | POST | 从多个 PPT 选页组合 |
| `/versions/{session_id}` | GET | 获取版本历史 |
| `/download/{session_id}/{version_id}` | GET | 下载指定版本 |
| `/download/{session_id}` | GET | 下载最新版本 |

### 课文生成 (`/api/v1/generate`)

| 端点 | 方法 | 功能 |
|------|------|------|
| `/outline` | POST | 根据课文生成大纲 |
| `/ppt` | POST | 根据大纲生成 PPTX |
| `/download/{gen_id}` | GET | 下载生成的 PPT |

### 配置 (`/api/v1/config`)

| 端点 | 方法 | 功能 |
|------|------|------|
| `/llm` | GET | 获取当前 LLM 配置 |
| `/llm` | POST | 保存 LLM 配置 |

---

## 关键技术点

### Run 级别文本替换

只修改 `<a:t>` 节点，保留 `<a:rPr>` 格式属性（字体、颜色、大小等），确保原始格式完整保留。

### 版本化管理

每次 AI 处理生成新版本，支持：
- 版本历史查看
- 任意版本下载
- 版本间对比

### OpenAI 兼容协议

支持多家 LLM 提供商，只需配置 `baseUrl` 和 `apiKey`：
- DeepSeek
- OpenAI
- 智谱 GLM
- 阿里云百炼
- Claude（通过代理）
- 其他 OpenAI 兼容 API

---

## 目录结构

```
ai-teaching-ppt/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── main.py         # FastAPI 入口
│   │   ├── config.py       # 配置管理
│   │   ├── api/            # HTTP 接口
│   │   │   ├── routes.py   # /ppt/* 端点
│   │   │   ├── generate.py # /generate/* 端点
│   │   │   └── config.py   # /config/* 端点
│   │   ├── core/           # PPTX 核心处理
│   │   │   ├── pptx_reader.py   # 解析 PPTX
│   │   │   ├── content_extractor.py # 提取文本
│   │   │   ├── pptx_writer.py   # 写回 PPTX
│   │   │   ├── style_applicator.py # 样式应用
│   │   │   └── animation_applicator.py # 动画应用
│   │   ├── ai/             # LLM 处理
│   │   │   ├── llm_client.py  # API 客户端
│   │   │   └── processor.py   # 处理编排
│   │   ├── services/       # 服务层
│   │   │   └── ppt_to_image.py # 预览图生成
│   │   └── models/         # 数据模型
│   ├── uploads/            # 上传文件存储
│   ├── public/             # 预览图存储
│   ├── requirements.txt
│   └── .env                # 环境配置
├── frontend/               # 前端服务
│   ├── src/
│   │   ├── app/           # Next.js App Router
│   │   │   ├── merge/     # PPT 合并页面
│   │   │   ├── generate/  # 课文生成页面
│   │   │   └── config/    # 配置页面
│   │   ├── components/    # React 组件
│   │   │   ├── merge/     # 合并功能组件
│   │   │   └── ui/        # 基础 UI 组件
│   │   ├── hooks/         # 自定义 Hooks
│   │   └── lib/           # 工具函数
│   └── package.json
└── docs/                   # 技术文档
```

---

## 常见问题

### Q: 预览图显示空白或加载失败？

**A**: 检查 LibreOffice 是否正确安装：
```bash
soffice --version
```
如果命令不存在，请参考上方安装说明安装 LibreOffice。

### Q: 上传 .ppt 文件提示转换失败？

**A**: 确保 LibreOffice 已安装，且 `soffice` 命令可用。或手动将 .ppt 转换为 .pptx 后上传。

### Q: AI 处理返回错误？

**A**: 检查以下几点：
1. `.env` 文件中的 `LLM_CONFIG` 是否正确配置
2. API Key 是否有效
3. `baseUrl` 是否正确
4. 查看后端日志获取详细错误信息

### Q: 前端无法连接后端？

**A**:
1. 确认后端服务已启动（http://localhost:9501/docs 可访问）
2. 检查前端 `src/lib/api.ts` 中的 `apiBaseUrl` 配置

---

## License

MIT