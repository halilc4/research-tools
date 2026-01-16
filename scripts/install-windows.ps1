# Research Tools MCP - Windows Installer
# Run: powershell -ExecutionPolicy Bypass -File install-windows.ps1

$ErrorActionPreference = "Stop"

Write-Host "`n=== Research Tools MCP Installer ===" -ForegroundColor Cyan

# =============================================================================
# PREREQUISITES
# =============================================================================

Write-Host "`n[1/4] Checking prerequisites..." -ForegroundColor Yellow

# --- Python ---
Write-Host "`nChecking Python..." -ForegroundColor Gray

$pythonPaths = @(
    "python",
    "python3",
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
    "$env:ProgramFiles\Python313\python.exe",
    "$env:ProgramFiles\Python312\python.exe",
    "$env:ProgramFiles\Python311\python.exe",
    "$env:ProgramFiles\Python310\python.exe"
)

$pythonPath = $null
foreach ($p in $pythonPaths) {
    try {
        $result = & $p --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $pythonPath = (Get-Command $p -ErrorAction SilentlyContinue).Source
            if (-not $pythonPath) { $pythonPath = $p }
            break
        }
    } catch {}
}

if ($pythonPath) {
    $pythonVersion = & $pythonPath --version 2>&1
    Write-Host "  Found Python: $pythonPath ($pythonVersion)" -ForegroundColor Green
} else {
    Write-Host "  Python not found. Installing..." -ForegroundColor Yellow

    $installed = $false

    # Try winget first
    if (-not $installed) {
        $wingetAvailable = Get-Command winget -ErrorAction SilentlyContinue
        if ($wingetAvailable) {
            Write-Host "  Installing via winget..." -ForegroundColor Gray
            winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements --silent
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
            $pythonPath = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
            if (Test-Path $pythonPath) { $installed = $true }
        }
    }

    # Try Chocolatey
    if (-not $installed) {
        $chocoAvailable = Get-Command choco -ErrorAction SilentlyContinue
        if ($chocoAvailable) {
            Write-Host "  Installing via Chocolatey..." -ForegroundColor Gray
            choco install python312 -y
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
            $pythonPath = "python"
            $installed = $true
        }
    }

    # Download and install manually
    if (-not $installed) {
        Write-Host "  Downloading Python installer..." -ForegroundColor Gray
        $installerUrl = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
        $installerPath = "$env:TEMP\python-installer.exe"

        Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing

        Write-Host "  Running Python installer (silent)..." -ForegroundColor Gray
        Start-Process -FilePath $installerPath -ArgumentList "/quiet", "InstallAllUsers=0", "PrependPath=1" -Wait

        Remove-Item $installerPath -Force -ErrorAction SilentlyContinue

        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        $pythonPath = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
        if (-not (Test-Path $pythonPath)) { $pythonPath = "python" }
        $installed = $true
    }

    if ($installed) {
        Write-Host "  Python installed." -ForegroundColor Green
    } else {
        Write-Host "  Failed to install Python." -ForegroundColor Red
        exit 1
    }
}

# --- uv ---
Write-Host "`nChecking uv..." -ForegroundColor Gray

$uvPaths = @(
    "uv",
    "$env:USERPROFILE\.local\bin\uv.exe",
    "$env:LOCALAPPDATA\uv\uv.exe",
    "$env:CARGO_HOME\bin\uv.exe",
    "$env:USERPROFILE\.cargo\bin\uv.exe"
)

$uvPath = $null
foreach ($u in $uvPaths) {
    try {
        $result = & $u --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $uvPath = $u
            if ($u -eq "uv") {
                $uvPath = (Get-Command uv -ErrorAction SilentlyContinue).Source
            }
            break
        }
    } catch {}
}

if ($uvPath) {
    $uvVersion = & $uvPath --version 2>&1
    Write-Host "  Found uv: $uvPath ($uvVersion)" -ForegroundColor Green
} else {
    Write-Host "  uv not found. Installing..." -ForegroundColor Yellow

    # Use official installer
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression

    # Find installed uv
    $possiblePaths = @(
        "$env:USERPROFILE\.local\bin\uv.exe",
        "$env:LOCALAPPDATA\uv\uv.exe",
        "$env:USERPROFILE\.cargo\bin\uv.exe"
    )

    foreach ($p in $possiblePaths) {
        if (Test-Path $p) {
            $uvPath = $p
            $parentDir = Split-Path $p -Parent
            $env:Path = "$parentDir;$env:Path"
            break
        }
    }

    if ($uvPath) {
        Write-Host "  uv installed: $uvPath" -ForegroundColor Green
    } else {
        Write-Host "  Failed to install uv." -ForegroundColor Red
        exit 1
    }
}

# Derive uvx path
$uvxPath = $uvPath -replace "uv\.exe$", "uvx.exe"
if (-not (Test-Path $uvxPath)) {
    $uvxPath = $uvPath -replace "uv$", "uvx"
}
Write-Host "  uvx path: $uvxPath" -ForegroundColor Gray

# =============================================================================
# API KEYS
# =============================================================================

Write-Host "`n[2/4] API Keys Configuration" -ForegroundColor Yellow
Write-Host "Press Enter to skip any key.`n"

$devtoKey = Read-Host "DEVTO_API_KEY (https://dev.to/settings/extensions)"
$serperKey = Read-Host "SERPER_API_KEY (https://serper.dev/api-key)"

# =============================================================================
# CONFIGURE CLAUDE DESKTOP
# =============================================================================

Write-Host "`n[3/4] Configuring Claude Desktop..." -ForegroundColor Yellow

$configDir = "$env:APPDATA\Claude"
$configPath = "$configDir\claude_desktop_config.json"

if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

# Use Python for JSON manipulation (works with all PowerShell versions)
& $pythonPath -c @"
import json
import os

config_path = r'$configPath'
uvx_path = r'$uvxPath'
devto_key = r'$devtoKey'
serper_key = r'$serperKey'

if os.path.exists(config_path) and os.path.getsize(config_path) > 0:
    with open(config_path, 'r') as f:
        config = json.load(f)
    print('  Found existing config, merging...')
else:
    config = {}

if 'mcpServers' not in config:
    config['mcpServers'] = {}

# Remove old version if exists
if 'research-tools' in config['mcpServers']:
    del config['mcpServers']['research-tools']
    print('  Removed old research-tools config.')

server_config = {
    'command': uvx_path,
    'args': ['--from', 'mcp-cli-research-tools[mcp]', 'rt-mcp']
}

env = {}
if devto_key:
    env['DEVTO_API_KEY'] = devto_key
if serper_key:
    env['SERPER_API_KEY'] = serper_key
if env:
    server_config['env'] = env

config['mcpServers']['research-tools'] = server_config

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print(f'  Config saved to: {config_path}')
"@
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Failed to configure Claude Desktop." -ForegroundColor Red
    exit 1
}

# =============================================================================
# RESTART CLAUDE DESKTOP
# =============================================================================

Write-Host "`n[4/4] Restarting Claude Desktop..." -ForegroundColor Yellow

$claudeProcess = Get-Process -Name "Claude" -ErrorAction SilentlyContinue
if ($claudeProcess) {
    Stop-Process -Name "Claude" -Force
    Start-Sleep -Seconds 2
}

$claudePath = "$env:LOCALAPPDATA\Programs\claude\Claude.exe"
if (Test-Path $claudePath) {
    Start-Process $claudePath
    Write-Host "  Claude Desktop restarted." -ForegroundColor Green
} else {
    Write-Host "  Claude Desktop not found. Please start manually." -ForegroundColor Yellow
}

# =============================================================================
# DONE
# =============================================================================

Write-Host "`n=== Installation Complete ===" -ForegroundColor Cyan
Write-Host @"

Summary:
  Python: $pythonPath
  uv:     $uvPath
  Config: $configPath

Research Tools MCP is now available in Claude Desktop.
"@
