【进程管理规则】
- 停止服务前检查 project_profile.json 的 services 配置
- 使用配置中的端口进行精确 kill
- 单次模式：收尾时停止所有后台服务
- 连续模式：保持服务运行供下个 session 使用

【跨平台命令】
- Windows: `netstat -ano | findstr :PORT` → `taskkill /F /T /PID <PID>`（/T 杀进程树，必须带）
- Linux/Mac: `lsof -ti :PORT | xargs kill -9`
- 跨平台备选: `npx kill-port PORT`
- PowerShell: `Get-NetTCPConnection -LocalPort PORT -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }`
- Python venv: uvicorn --reload 产生父子进程树，必须用 /T 或杀父进程
