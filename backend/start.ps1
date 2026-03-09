# 单进程生产环境启动脚本 (Windows)
# 解决 uvicorn --reload 多进程导致的 SSE/网络异常问题

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# 确保端口未被占用
Write-Host "【环境清理】检查并释放 8000 端口..."
$proc = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -First 1
if ($proc) {
    Stop-Process -Id $proc.OwningProcess -Force -ErrorAction SilentlyContinue
    Write-Host "已终止占用 8000 端口的进程"
}
Start-Sleep -Seconds 1

# 使用单进程模式启动（无 reload，适合生产/测试）
Write-Host "【启动】uvicorn 单进程模式..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --no-access-log
