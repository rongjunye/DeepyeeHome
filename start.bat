@echo off
rem ============================================================
rem  NeuroArchAI Platform 双击启动
rem  直接双击本文件即可，无需在终端敲命令
rem ============================================================
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  正在启动 NeuroArchAI Platform ...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
echo.
echo  服务已停止。
pause
