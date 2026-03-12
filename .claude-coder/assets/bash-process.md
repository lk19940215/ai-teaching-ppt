【进程管理规则】
- 停止服务前检查 project_profile.json 的 services 配置
- 使用配置中的端口进行精确 kill
- 单次模式：收尾时停止所有后台服务
- 连续模式：保持服务运行供下个 session 使用