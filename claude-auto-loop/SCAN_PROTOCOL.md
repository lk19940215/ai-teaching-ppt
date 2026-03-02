<!-- 
  Scan Protocol for Claude Auto Loop.
  Only injected during run_scan() — not used in coding sessions.
  Contains: scan steps, project_profile.json format, init.sh generation rules.
-->

# 项目扫描协议（首次运行时执行）

当 `project_profile.json` 不存在时，按以下步骤扫描项目并生成配置文件。

## 步骤 1：判断项目类型

检查项目根目录：
- 如果存在代码文件（`.py`, `.js`, `.ts`, `package.json`, `requirements.txt` 等）→ **旧项目**（已有代码）
- 如果根目录几乎为空（仅有 `claude-auto-loop/` 和少量文件）→ **新项目**（从零开始）

## 步骤 2A：旧项目 — 扫描现有代码，**优先整理文档**

**文档先行**：旧项目在扫描前，必须先确保项目文档可读、可用。若 `README.md` 缺失或过于简略、`docs/` 不完整，**先补充/整理文档**（README 至少含项目简介、技术栈、目录结构、关键模块说明），再继续扫描。文档是后续任务高质量执行的基础。

按顺序检查以下文件，**存在则读取**，不存在则跳过：

1. `package.json` → Node.js 项目，读取 dependencies 判断框架（React/Vue/Express 等）
2. `pyproject.toml` / `requirements.txt` / `setup.py` / `setup.cfg` → Python 项目，判断框架（FastAPI/Django/Flask 等）
3. `Cargo.toml` → Rust，`go.mod` → Go，`pom.xml` / `build.gradle` → Java
4. `docker-compose.yml` / `Dockerfile` → 容器化配置，提取服务定义
5. `Makefile` → 构建方式
6. `README.md` / `docs/` → 现有文档（若缺失或过简，**先整理再扫描**；在 progress.txt 中记录文档状态）
7. `.env` / `.env.example` → 环境变量配置
8. 运行 `ls` 查看顶层目录结构

根据扫描结果，生成 `project_profile.json`（格式见下方）和 `init.sh`（规则见下方）。`existing_docs` 须如实列出项目中**所有**可读文档路径。

## 步骤 2B：新项目 — 脚手架搭建

1. **优先检查项目根目录是否存在 `requirements.md`**，如果存在，以其中的技术约束和设计要求为准
2. 根据需求（`requirements.md` 或 harness 传入的需求文本），设计技术架构
3. 创建项目目录结构和基础文件（入口文件、配置文件、依赖文件等）
4. 生成 `README.md`，说明项目用途和技术栈
5. 初始化包管理（`npm init` / `pip freeze` 等）
6. 完成后，执行**步骤 2A 的扫描流程**生成 `project_profile.json` 和 `init.sh`

## 步骤 3：生成 tasks.json

根据用户需求（优先参考 `requirements.md`，其次参考 harness 传入的需求文本），将功能分解为具体任务（格式见 CLAUDE.md 中的 tasks.json 章节）。如果 `requirements.md` 中有明确的功能列表，按其内容拆分；如果只有模糊描述，自行合理拆分。

**重要：避免任务与脚手架重叠**。步骤 2B 中已创建的代码（目录结构、入口文件、配置文件、依赖文件、README）不应重复出现在 tasks.json 中。tasks.json 的第一个任务应从脚手架之后的「第一个有业务逻辑的功能」开始。infra 类任务（如 Docker 配置、CI/CD）应合并为尽量少的条目。

## 步骤 4：收尾

1. 创建 `progress.txt`，记录初始化摘要
2. 写入 `session_result.json`
3. `git add -A && git commit -m "init: 项目扫描 + 任务分解"`

---

## project_profile.json 格式

```json
{
  "name": "项目名称（从 package.json 或目录名自动检测）",
  "detected_at": "2026-02-13T10:00:00",
  "project_type": "existing | new",
  "tech_stack": {
    "languages": ["python", "typescript"],
    "backend": {
      "framework": "fastapi | django | express | none",
      "runtime": "uvicorn | gunicorn | node | none",
      "entry": "main:app | app.py | index.js"
    },
    "frontend": {
      "framework": "react | vue | none",
      "bundler": "vite | webpack | none",
      "dir": "web | frontend | client | ."
    },
    "database": "mongodb | postgresql | sqlite | none",
    "package_managers": ["pip", "npm", "cargo"]
  },
  "services": [
    {
      "name": "backend",
      "command": "启动命令",
      "port": 8000,
      "health_check": "http://localhost:8000/health",
      "cwd": "."
    },
    {
      "name": "frontend",
      "command": "npm run dev",
      "port": 5173,
      "health_check": "http://localhost:5173",
      "cwd": "web"
    }
  ],
  "env_setup": {
    "python_env": "conda:env_name | venv | system",
    "node_version": "20 | 18 | none"
  },
  "existing_docs": ["README.md", "docs/api.md"],
  "has_tests": false,
  "has_docker": false,
  "mcp_tools": {
    "playwright": false
  },
  "scan_files_checked": [
    "package.json", "pyproject.toml", "requirements.txt",
    "Dockerfile", "docker-compose.yml", "Makefile", "README.md"
  ]
}
```

**注意**：
- `existing_docs`：列出项目中所有可读文档路径，Agent 实现前按需读取与任务相关的文档；扫描时须如实填写全部文档
- 字段值必须基于实际扫描结果，**禁止猜测**
- 如果某个字段无法确定，使用 `"none"` 或空数组 `[]`
- `services` 中的 `command` 必须来自实际的配置文件（package.json scripts、Procfile 等）或标准命令
- `mcp_tools` 字段：检查 `claude-auto-loop/config.env` 中的 `MCP_PLAYWRIGHT` 等变量。如果 `config.env` 不存在，则全部设为 `false`

---

## init.sh 生成规则

扫描完成后，基于 `project_profile.json` 生成 `init.sh`，遵循以下规则：

1. **文件头部**：包含 `#!/bin/bash`、`set -e`、脚本说明
2. **环境激活**：
   - 如果 `env_setup.python_env` 以 `conda:` 开头 → 生成 conda activate 逻辑（需 source conda.sh）
   - 如果 `env_setup.python_env` 是 `venv` → 生成 `source .venv/bin/activate`
   - 如果 `env_setup.node_version` 不是 `none` → 生成 nvm use 逻辑
3. **服务启动**：对 `services` 数组中的每个服务：
   - 先用 `lsof -i :端口` 检查是否已运行
   - 未运行则 `nohup 命令 > /tmp/日志文件 2>&1 &`
   - 等待健康检查通过（最多 10 秒）
4. **幂等设计**：已运行的服务必须跳过，不能重复启动
5. **末尾输出**：打印所有服务的 URL
