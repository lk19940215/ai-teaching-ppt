# Claude 全局配置

接入 阿里Coding Plan后，Claude 全局配置如下：

```json
{
  "permissions": {
    "allow": [
      "Bash",
      "Read",
      "Write",
      "Edit",
      "MultiEdit",
      "Grep",
      "Glob",
      "LS",
      "WebFetch",
      "WebSearch",
      "Task",
      "TodoWrite",
      "NotebookRead",
      "NotebookEdit",
      "mcp__pencil",
      "mcp__playwright"
    ]
  },
  "skipDangerousModePermissionPrompt": true,
  "env": {
    "API_TIMEOUT_MS": "3000000",
    "ANTHROPIC_BASE_URL": "https://coding.dashscope.aliyuncs.com/apps/anthropic",
    "ANTHROPIC_API_KEY": "sk-sp-",
    "ANTHROPIC_MODEL": "glm-5",
    "ANTHROPIC_SMALL_FAST_MODEL": "MiniMax-M2.5",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "qwen3-max-2026-01-23",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "qwen3-coder-next",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "qwen3-coder-plus"
  }
}
```

# Claude技巧

[快查文档](https://code.claude.com/docs/zh-CN/interactive-mode)

## 配置MCP全项目通用配置

windows 下，在 用户目录/.claude.json 中配置如下：
Mac 下，在 ~/.claude.json 中配置如下：

```json
{
  "mcpServers": {
    "playwright": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"],
      "env": {}
    }
  }
}
```
## 快捷键快查

- 快捷键快查

  帮助快速输入，查看输出信息
```bash
------------------------------------
Ctrl+G        // 在默认文本编辑器中打开 -> 用于编辑复杂命令
Ctrl+O        // 切换详细输出 -> 用于查看详细输出
Ctrl+R        // 搜索命令历史 -> 用于搜索输入prompt的历史
Ctrl+R        // 反向搜索命令历史
Option+P（macOS）或 Alt+P       // 在不清除提示的情况下切换模型
Ctrl+K          // 删除到行尾
Ctrl+L          // 清除所有内容
Ctrl+U          // 删除整行
------------------------------------
```


- 常用命令快查

```bash
Shift+Tab       // 在自动接受模式、Plan Mode 和正常模式之间切换。
/review         // 审查拉取请求的代码质量、正确性、安全性和测试覆盖率。传递 PR 编号，或省略以列出打开的 PR。
/memory         // 查看记忆内容
/clear          // 清除记忆内容
/model          // 查看当前模型
/plan           // 切换Plan Mode
```

- 内置技能

```bash
/simplify       // 简化/重构模式
/debug          // 调试模式
```

# 高阶用法

## Sub-agent 用法

[Sub-agent 用法](https://code.claude.com/docs/zh-CN/sub-agents#plan)

## hook 用法

hook 用法，用于在 Claude 执行特定操作时，触发通知。 
```bash
[触发通知的 hook 示例](https://code.claude.com/docs/zh-CN/hooks#notification)

```

# 其它

## 2026-03-09

### 问题
- playwright mcp与 playwright test/ cli 的对比
    进过对比，发现 playwright mcp 的测试能力更强，适用于不稳定、复杂的测试场景。可以让AI自我发现问题。而其它测试工具，如 playwright test/ cli ，则更适用于确认性的场景。