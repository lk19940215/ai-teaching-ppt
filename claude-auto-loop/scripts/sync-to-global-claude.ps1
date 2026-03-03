# claude-auto-loop - Sync Config to Global Claude Settings
# Usage: powershell -ExecutionPolicy Bypass -File claude-auto-loop\scripts\sync-to-global-claude.ps1

$configPath = "claude-auto-loop\config.env"
# Check common locations for config.env
if (-not (Test-Path $configPath)) {
    # If run from scripts/ subdirectory
    $parentPath = Join-Path $PSScriptRoot "..\config.env"
    if (Test-Path $parentPath) {
        $configPath = $parentPath
    } else {
         # If run from project root but looking in claude-auto-loop
         if (Test-Path "$PSScriptRoot\config.env") {
             $configPath = "$PSScriptRoot\config.env"
         } else {
             Write-Error "Could not find config.env"
             exit 1
         }
    }
}

$settingsPath = "$env:USERPROFILE\.claude\settings.json"

Write-Host "Reading config from: $configPath" -ForegroundColor Gray

$envVars = @{}
$lines = Get-Content $configPath
foreach ($line in $lines) {
    if ($line -match "^(?<key>[A-Z_]+)=(?<value>.*)$") {
        $envVars[$matches.key] = $matches.value.Trim()
    }
}

$claudeConfig = @{}
if (Test-Path $settingsPath) {
    try {
        $jsonContent = Get-Content $settingsPath -Raw -ErrorAction SilentlyContinue
        if ($jsonContent) {
            $json = $jsonContent | ConvertFrom-Json
            if ($json) {
                foreach ($prop in $json.PSObject.Properties) {
                    $claudeConfig[$prop.Name] = $prop.Value
                }
            }
        }
    } catch {
        Write-Warning "Failed to parse settings.json"
    }
} else {
    $claudeDir = Split-Path $settingsPath
    if (-not (Test-Path $claudeDir)) {
        New-Item -Path $claudeDir -ItemType Directory | Out-Null
    }
}

# Clean old invalid top-level keys
$invalidKeys = @("apiKey", "anthropicBaseUrl", "defaultSonnetModel", "defaultOpusModel", "defaultHaikuModel", "model")
foreach ($key in $invalidKeys) {
    if ($claudeConfig.ContainsKey($key)) {
        $claudeConfig.Remove($key)
        Write-Host "Removed invalid top-level key: $key" -ForegroundColor Magenta
    }
}

# Ensure env object exists
if (-not $claudeConfig.ContainsKey("env")) {
    $claudeConfig["env"] = @{}
}

# Convert PSCustomObject to Hashtable if needed
if ($claudeConfig["env"] -is [System.Management.Automation.PSCustomObject]) {
    $newEnv = @{}
    foreach ($prop in $claudeConfig["env"].PSObject.Properties) {
        $newEnv[$prop.Name] = $prop.Value
    }
    $claudeConfig["env"] = $newEnv
}

# Sync config to env
foreach ($key in $envVars.Keys) {
    if ($key.StartsWith("ANTHROPIC_") -or $key -match "_TIMEOUT_MS$" -or $key -eq "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC") {
        # Skip ANTHROPIC_AUTH_TOKEN if present in config (legacy) unless specifically needed
        if ($key -eq "ANTHROPIC_AUTH_TOKEN" -and $envVars["MODEL_PROVIDER"] -eq "aliyun-coding") {
             continue 
        }

        $claudeConfig["env"][$key] = $envVars[$key]
        Write-Host "Set env.$key" -ForegroundColor Cyan
    }
}

# Remove legacy/conflicting env vars if present
if ($claudeConfig["env"].ContainsKey("ANTHROPIC_AUTH_TOKEN") -and $envVars["MODEL_PROVIDER"] -eq "aliyun-coding") {
    $claudeConfig["env"].Remove("ANTHROPIC_AUTH_TOKEN")
    Write-Host "Removed legacy env.ANTHROPIC_AUTH_TOKEN" -ForegroundColor Magenta
}

# Write JSON without BOM (using UTF8Encoding(false))
$jsonOutput = $claudeConfig | ConvertTo-Json -Depth 5
[System.IO.File]::WriteAllText($settingsPath, $jsonOutput, [System.Text.UTF8Encoding]::new($false))
Write-Host "Updated Claude Global Config: $settingsPath" -ForegroundColor Green
