项目类型: {{projectType}}

按系统协议中的「项目扫描协议」执行步骤 1-3。

profile 质量要求（harness 会校验）：
- services 数组必须包含所有可启动服务（command、port、health_check），不得为空
- existing_docs 必须列出所有实际存在的文档路径
- 检查 .claude/CLAUDE.md 是否存在，若无则生成（WHAT/WHY/HOW 格式），并加入 existing_docs

注意：本次只扫描项目，不分解任务。
