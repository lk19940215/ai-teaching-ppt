Session {{sessionNum}}。执行 6 步流程。
效率要求：先规划后编码，完成全部编码后再统一测试，禁止编码-测试反复跳转。后端任务用 curl 验证，不启动浏览器。
{{mcpHint}}
{{testHint}}
{{docsHint}}
{{envHint}}
{{taskHint}}
{{testEnvHint}}
{{playwrightAuthHint}}
{{memoryHint}}
{{serviceHint}}

可用工具与使用规范（严格遵守）：
- 搜索文件名: Glob（如 **/*.ts），禁止 bash find
- 搜索文件内容: Grep（正则，基于 ripgrep），禁止 bash grep
- 读文件: Read（支持批量多文件同时读取），禁止 bash cat/head/tail
- 列目录: LS，禁止 bash ls
- 编辑文件: 同一文件多处修改用 MultiEdit（一次原子调用），单处用 Edit
- 复杂搜索: Task（启动子 Agent 并行搜索，不消耗主 context），适合开放式探索
- 查文档/API: WebSearch + WebFetch
- 效率: 多个 Read/Glob/Grep 尽量合并为一次批量调用，减少工具轮次

进程管理规范（跨平台，严格遵守）：
- 停止端口服务（Windows）: `netstat -ano | findstr :PORT` 获取 PID，然后 `taskkill /F /T /PID <PID>`（/T 杀进程树，必须带 /T）
- 停止端口服务（Linux/Mac）: `lsof -ti :PORT | xargs kill -9`
- 备选方案: `npx kill-port PORT`（跨平台）或 `powershell -Command "Get-NetTCPConnection -LocalPort PORT -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"`
- 杀进程失败时不要反复重试同一命令（最多 2 次），立即换用其他方法
- 重启服务前必须先确认端口已释放（netstat/lsof 无输出），再启动新进程
- Python venv 环境注意：uvicorn --reload 会创建父子进程树，必须用 /T 参数或杀父进程

完成后写入 session_result.json。{{retryContext}}
