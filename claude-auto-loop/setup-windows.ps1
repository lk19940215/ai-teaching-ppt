# Claude Auto Loop - Windows Environment Setup
# Configures both PowerShell Profile and CMD AutoRun to prefer Git Bash over WSL bash.
#
# Usage: powershell -ExecutionPolicy Bypass -File claude-auto-loop\setup-windows.ps1

Write-Host "=== Claude Auto Loop - Windows Setup ===" -ForegroundColor Cyan

# 1. Locate Git Bash
Write-Host "Locating Git Bash..."
$gitPath = Get-Command git -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if (-not $gitPath) {
    Write-Error "Git not found. Please install Git for Windows: https://git-scm.com/download/win"
    exit 1
}

$gitRoot = (Get-Item $gitPath).Directory.Parent.FullName
$bashPath = Join-Path $gitRoot "bin\bash.exe"
$binDir = Join-Path $gitRoot "bin"

if (-not (Test-Path $bashPath)) {
    $defaultPaths = @(
        "C:\Program Files\Git\bin\bash.exe",
        "C:\Program Files (x86)\Git\bin\bash.exe",
        "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe"
    )
    foreach ($p in $defaultPaths) {
        if (Test-Path $p) {
            $bashPath = $p
            $binDir = (Get-Item $p).Directory.FullName
            break
        }
    }
}

if (-not (Test-Path $bashPath)) {
    Write-Error "Git Bash not found. Please ensure Git is installed correctly."
    exit 1
}

Write-Host "Found Git Bash at: $bashPath" -ForegroundColor Green

# 2. Check current bash resolution
$currentBash = Get-Command bash -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
$needFix = $true

if ($currentBash -and $currentBash.ToLower() -eq $bashPath.ToLower()) {
    Write-Host "Current bash already points to Git Bash." -ForegroundColor Green
    $needFix = $false
} elseif ($currentBash) {
    Write-Host "Current bash points to: $currentBash (likely WSL)" -ForegroundColor Yellow
} else {
    Write-Host "No bash command found currently." -ForegroundColor Yellow
}

# 3a. Configure PowerShell Profile
Write-Host "`n--- PowerShell ---"
$profilePath = $PROFILE
if (-not (Test-Path $profilePath)) {
    $profileDir = Split-Path $profilePath
    if (-not (Test-Path $profileDir)) {
        New-Item -Path $profileDir -ItemType Directory -Force | Out-Null
    }
    Write-Host "Creating PowerShell Profile: $profilePath"
    New-Item -Path $profilePath -ItemType File -Force | Out-Null
}

$profileContent = Get-Content $profilePath -Raw -ErrorAction SilentlyContinue
$pathConfig = '$env:PATH = "' + $binDir + ';" + $env:PATH'

if ($profileContent -and $profileContent.Contains($binDir)) {
    Write-Host "PowerShell Profile: already configured." -ForegroundColor Green
} else {
    Write-Host "Adding Git Bash path to PowerShell Profile..."
    Add-Content -Path $profilePath -Value "`n# Claude Auto Loop: Prefer Git Bash"
    Add-Content -Path $profilePath -Value $pathConfig
    Write-Host "PowerShell Profile: done." -ForegroundColor Green
}

# 3b. Configure CMD AutoRun (registry key)
Write-Host "`n--- CMD ---"
$regPath = "HKCU:\SOFTWARE\Microsoft\Command Processor"
$autoRunCmd = "set ""PATH=$binDir;%PATH%"""

$currentAutoRun = Get-ItemProperty -Path $regPath -Name AutoRun -ErrorAction SilentlyContinue | Select-Object -ExpandProperty AutoRun -ErrorAction SilentlyContinue

if ($currentAutoRun -and $currentAutoRun.Contains($binDir)) {
    Write-Host "CMD AutoRun: already configured." -ForegroundColor Green
} else {
    if ($currentAutoRun) {
        $newAutoRun = "$autoRunCmd && $currentAutoRun"
    } else {
        $newAutoRun = $autoRunCmd
    }
    Set-ItemProperty -Path $regPath -Name AutoRun -Value $newAutoRun
    Write-Host "CMD AutoRun: done." -ForegroundColor Green
    Write-Host "  Registry: $regPath\AutoRun" -ForegroundColor DarkGray
}

# Apply to current session immediately
if ($needFix) {
    $env:PATH = "$binDir;" + $env:PATH
    Write-Host "`nCurrent session PATH updated." -ForegroundColor Green
}

# 4. Verification
$finalBash = Get-Command bash -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
Write-Host ""
if ($finalBash -and $finalBash.ToLower() -eq $bashPath.ToLower()) {
    Write-Host "Setup successful!" -ForegroundColor Green
    Write-Host "After restarting terminals, bash will point to Git Bash in both PowerShell and CMD."
    Write-Host ""
    Write-Host "You can then run:"
    Write-Host "  bash claude-auto-loop/run.sh"
    Write-Host "  bash claude-auto-loop/setup.sh"
} else {
    Write-Host "Setup written. Please restart your terminal for changes to take effect." -ForegroundColor Yellow
    Write-Host "Expected bash: $bashPath"
}
