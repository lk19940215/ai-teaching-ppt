# 任务分解指南

> 本文档是 `claude-coder add` 指令的参考文档。
> ADD Agent 的唯一职责：分解需求为结构化任务，追加到 tasks.json。不实现任何代码。

---

## tasks.json 格式

```json
{
  "project": "项目名称",
  "created_at": "2026-02-13",
  "features": [
    {
      "id": "feat-001",
      "category": "backend | frontend | fullstack | infra",
      "priority": 1,
      "description": "功能的简要描述（40字内）",
      "steps": [
        "具体步骤 1",
        "具体步骤 2",
        "端到端测试：验证方法"
      ],
      "status": "pending",
      "depends_on": []
    }
  ]
}
```

### 字段规范

| 字段 | 规则 |
|------|------|
| `id` | 格式 `feat-NNN`，从已有最大值递增 |
| `category` | `backend` / `frontend` / `fullstack` / `infra`，准确归类 |
| `priority` | 数字越小越优先，从已有最大值递增 |
| `description` | 简明扼要，40 字内，说明"做什么"而非"怎么做" |
| `steps` | 具体可操作步骤，最后一步必须是可验证的测试命令，单任务不超过 5 步 |
| `status` | 新增任务一律 `"pending"` |
| `depends_on` | 引用前置任务的 `id`，形成 DAG（有向无环图），不得循环依赖 |

---

## 任务分解规则

### 粒度控制

- 每个任务是独立可测试的功能单元，1-3 session 可完成，新增不超 500 行
- 单任务 steps 不超过 5 步，超过则拆分为多个任务
- 第一个任务从第一个有业务逻辑的功能开始，不重复脚手架内容
- 新项目：infra 任务合并为尽量少的条目，不拆碎

### 验证命令模板

steps 的最后一步必须包含可执行的验证命令：

```
API:   curl -s -o /dev/null -w "%{http_code}" http://localhost:PORT/path → 200
文件:  grep -q "关键内容" path/to/file && echo "pass"
构建:  npm run build 2>&1 | tail -1 → 无 error
页面:  Playwright MCP snapshot 验证关键元素存在
```

### 反面案例（禁止出现）

- `"实现用户功能"` → 太模糊，应拆为具体接口
- `"编写测试"` → 测试应内嵌在 steps 末尾，不是独立任务
- steps 只有 `"实现xxx"` 没有验证步骤

---

## requirements.md 处理原则

`requirements.md` 是用户的需求输入，**绝对不能修改它**。但"不能改"不等于"必须盲从"。遇到以下情况时，在 `session_result.json` 的 `notes` 中记录问题，按最合理的方式继续分解：

| 场景 | 处理方式 |
|------|----------|
| 需求自相矛盾 | 记录矛盾，按技术可行的方案分解，说明选择理由 |
| 需求与已有代码冲突 | 记录冲突，说明重构成本，按现有架构分解，建议用户确认 |
| 需求太模糊无法执行 | 自行做出合理决策，在 notes 中记录选择，供用户确认 |
| 需求中途变更 | 记录变更影响，基于最新需求分解 |
| 需求引用了不可访问的资源 | 记录问题，根据文字描述尽力分解 |
| 需求指定了不存在的依赖 | 记录问题，使用最接近的可用版本 |

**核心原则：不停工、不擅改、留记录。**

---

## Playwright MCP 测试任务

当任务涉及前端或全栈端到端测试，且项目已配置 Playwright MCP 时，测试步骤的详细规范（结构化标签、Smart Snapshot 策略、SSE 等待模式、步骤模板等）统一参见 `.claude-coder/test_rule.md` 第五节（等待策略）和第八节（步骤模板）。

此处只列关键原则：
- steps 首步加入 `【规则】阅读 .claude-coder/test_rule.md`
- 使用 `【P0】【P1】【P2】` 标记优先级，预算不足时可按优先级裁剪
- 长等待操作使用 `browser_wait_for` 而非轮询 snapshot
