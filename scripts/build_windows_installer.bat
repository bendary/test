@echo off
setlocal

set "APP_NAME=%~1"
set "APP_VERSION=%~2"

if "%APP_NAME%"=="" set "APP_NAME=ShiqiAutoWin"
if "%APP_VERSION%"=="" set "APP_VERSION=0.1.0"

set "PS_SCRIPT=%~dp0build_windows_installer.ps1"
if not exist "%PS_SCRIPT%" (
  echo [ERROR] 未找到脚本: %PS_SCRIPT%
  exit /b 1
)

powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%" -AppName "%APP_NAME%" -AppVersion "%APP_VERSION%"
if errorlevel 1 (
  echo [ERROR] 打包失败
  exit /b %errorlevel%
)

echo [OK] 打包完成
endlocal
