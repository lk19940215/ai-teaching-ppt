# Claude Auto Loop - Windows Environment Setup
# Configures PowerShell Profile to prefer Git Bash over WSL/System32 bash.
#
# Usage: .\claude-auto-loop\setup-windows.ps1

Write-Host "=== Claude Auto Loop - Windows Setup ===" -ForegroundColor Cyan

# 1. Locate Git Bash
Write-Host "Locating Git Bash..."
$gitPath = Get-Command git -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if (-not $gitPath) {
    Write-Error "Git not found. Please install Git for Windows: https://git-scm.com/download/win"
    exit 1
}

# Deduce bin directory (from .../cmd/git.exe to .../bin/bash.exe)
$gitRoot = (Get-Item $gitPath).Directory.Parent.FullName
$bashPath = Join-Path $gitRoot "bin\bash.exe"
$binDir = Join-Path $gitRoot "bin"

if (-not (Test-Path $bashPath)) {
    # Try default paths
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
    Write-Host "Current bash is already pointing to Git Bash." -ForegroundColor Green
    $needFix = $false
} elseif ($currentBash) {
    Write-Host "Current bash points to: $currentBash (likely WSL)" -ForegroundColor Yellow
} else {
    Write-Host "No bash command found currently." -ForegroundColor Yellow
}

# 3. Configure PowerShell Profile
if ($needFix) {
    $profilePath = $PROFILE
    # Check if Profile exists
    if (-not (Test-Path $profilePath)) {
        # Ensure directory exists
        $profileDir = Split-Path $profilePath
        if (-not (Test-Path $profileDir)) {
            New-Item -Path $profileDir -ItemType Directory -Force | Out-Null
        }
        Write-Host "Creating PowerShell Profile: $profilePath"
        New-Item -Path $profilePath -ItemType File -Force | Out-Null
    }

    $profileContent = Get-Content $profilePath -Raw
    $pathConfig = '$env:PATH = "' + $binDir + ';" + $env:PATH'
    
    # Check if already configured
    if ($profileContent -match [regex]::Escape($binDir)) {
        Write-Host "Profile already contains Git Bash path configuration." -ForegroundColor Yellow
    } else {
        Write-Host "Adding Git Bash path to Profile..."
        Add-Content -Path $profilePath -Value "`n# Claude Auto Loop: Prefer Git Bash"
        Add-Content -Path $profilePath -Value $pathConfig
        Write-Host "Configuration written." -ForegroundColor Green
        
        # Apply to current session immediately
        $env:PATH = "$binDir;" + $env:PATH
        Write-Host "Current session PATH updated." -ForegroundColor Green
    }
}

# 4. Verification
$finalBash = Get-Command bash -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if ($finalBash -and $finalBash.ToLower() -eq $bashPath.ToLower()) {
    Write-Host "`nEnvironment setup successful!" -ForegroundColor Green
    Write-Host "You can now run .sh scripts directly, e.g.:"
    Write-Host "  bash claude-auto-loop/run.sh"
    Write-Host "  bash claude-auto-loop/setup.sh"
} else {
    Write-Host "`nWarning: Configuration might not be fully effective. Please restart PowerShell." -ForegroundColor Yellow
    Write-Host "Expected bash: $bashPath"
    Write-Host "Actual bash: $finalBash"
}
