# 核心协议（所有会话共享）

## 铁律（不可违反）

1. **每次结束前必须 git commit**：确保文件不丢失
2. **每次结束前必须写 session_result.json**：这是 harness 校验你工作成果的唯一依据
3. **不得修改 requirements.md**：这是用户的需求输入，只能读取和遵循
4. **project_profile.json 基于事实**：所有字段必须来自实际文件扫描，禁止猜测或编造

## session_result.json 格式

```json
{
  "session_result": "success | failed",
  "status_before": "pending | failed | N/A",
  "status_after": "done | failed | in_progress | testing | N/A",
  "notes": "未解决的阻塞问题或关键技术决策（无则留空，不要复述已完成的工作）"
}
```

## 关键文件（全局）

| 文件 | 用途 | 权限 |
|---|---|---|
| `.claude/CLAUDE.md` | 项目指令（SDK 自动加载） | 只读 |
| `requirements.md` | 用户需求文档 | **只读** |
| `.claude-coder/project_profile.json` | 项目元数据（技术栈、服务等） | 只读（scan 时可创建） |
| `.claude-coder/session_result.json` | 本次会话结构化输出 | 覆盖写入 |
| `.claude-coder/progress.json` | 跨会话记忆日志（harness 维护） | 只读 |
