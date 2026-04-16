$ErrorActionPreference = "Stop"

$Repo = "https://github.com/simparfy/GCBC.git"
$DefaultDir = Join-Path $env:USERPROFILE ".gcbc"

Write-Host "=== GCBC Installer ===" -ForegroundColor Cyan
Write-Host ""

# Allow override via GCBC_DIR env var
$InstallDir = if ($env:GCBC_DIR) { $env:GCBC_DIR } else { $DefaultDir }

# Check Python
try {
    $pyVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
    $parts = $pyVersion -split '\.'
    if ([int]$parts[0] -lt 3 -or ([int]$parts[0] -eq 3 -and [int]$parts[1] -lt 11)) {
        Write-Host "Error: Python >= 3.11 required, found $pyVersion" -ForegroundColor Red
        exit 1
    }
    Write-Host "Python $pyVersion - OK" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is required (>= 3.11). Install from https://python.org" -ForegroundColor Red
    exit 1
}

# Check git
try {
    git --version | Out-Null
} catch {
    Write-Host "Error: git is required. Install from https://git-scm.com" -ForegroundColor Red
    exit 1
}

# Clone or update
if (Test-Path (Join-Path $InstallDir ".git")) {
    Write-Host "Existing installation found at $InstallDir - updating ..."
    git -C $InstallDir pull origin main
} else {
    Write-Host "Cloning GCBC to $InstallDir ..."
    git clone $Repo $InstallDir
}

# Install
Write-Host "Installing Python package ..."
python -m pip install -e $InstallDir --quiet

# Verify
try {
    $versionJson = gcbc version 2>$null | ConvertFrom-Json
    $version = $versionJson.version
    Write-Host ""
    Write-Host "GCBC v$version installed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Get started:"
    Write-Host "  gcbc --help"
    Write-Host "  gcbc version"
} catch {
    Write-Host ""
    Write-Host "Installation complete, but 'gcbc' not found on PATH." -ForegroundColor Yellow
    Write-Host "You may need to add your Python Scripts directory to PATH."
    Write-Host "Try: python -m gcbc.cli --help"
}
