param(
    [string]$AppName = "ShiqiAutoWin",
    [string]$AppVersion = "0.1.0"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "未检测到 uv，请先安装 uv: https://docs.astral.sh/uv/getting-started/installation/"
}

Write-Host "==> Sync uv environment"
uv sync

Write-Host "==> Build Windows app (PyInstaller onedir)"
uv run pyinstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onedir `
    --name $AppName `
    --paths src `
    --collect-all airtest `
    --collect-all pywinauto `
    --add-data "scripts;scripts" `
    --add-data "notes;notes" `
    src/app/main.py

$isccCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
)
$iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) {
    throw "未找到 Inno Setup 6 (ISCC.exe)。请先安装 Inno Setup 6。"
}

Write-Host "==> Build installer (.exe)"
& $iscc `
    "/DAppName=$AppName" `
    "/DAppVersion=$AppVersion" `
    "/DProjectRoot=$ProjectRoot" `
    "$PSScriptRoot\windows_installer.iss"

$portableDir = Join-Path $ProjectRoot "dist\$AppName"
$installerDir = Join-Path $ProjectRoot "dist\installer"
Write-Host "Build complete:"
Write-Host ("Portable app: {0}" -f $portableDir)
Write-Host ("Installer: {0}" -f $installerDir)
