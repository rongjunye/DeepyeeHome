<#
.SYNOPSIS
    一键启动 NeuroArchAI Platform。

.DESCRIPTION
    用于解决「终端里 python 命令不可用」的情况：
    脚本会在多个常见位置自动寻找 Python，找不到再提示安装。
    找到后会先检查依赖，然后启动服务。

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File start.ps1
#>

$ErrorActionPreference = "Stop"

function Write-Step($text) { Write-Host "==> $text" -ForegroundColor Cyan }
function Write-Ok($text) { Write-Host "    $text" -ForegroundColor Green }
function Write-Warn($text) { Write-Host "    $text" -ForegroundColor Yellow }
function Write-Fail($text) { Write-Host "    $text" -ForegroundColor Red }

# 脚本位于项目根目录
$repoRoot = $PSScriptRoot
Set-Location $repoRoot

Write-Step "定位 Python"

$candidates = @()
$cmd = Get-Command python -ErrorAction SilentlyContinue
if ($cmd) { $candidates += $cmd.Source }

# 常见安装位置（含 Loomy 内置运行时）
$candidates += (Join-Path $env:LOCALAPPDATA "Loomy\python-runtime\3.13.13-09efd5c6\python.exe")
$candidates += (Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe")
$candidates += (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe")
$candidates += "C:\Python313\python.exe"
$candidates += "C:\Python312\python.exe"

$python = $null
foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path $candidate)) { $python = $candidate; break }
}

if (-not $python) {
    Write-Fail "未找到可用的 Python。"
    Write-Host "请先安装 Python 3.10 或更高版本："
    Write-Host "  方式一（推荐）：winget install --id Python.Python.3.13 -e"
    Write-Host "  方式二：https://www.python.org/downloads/"
    exit 1
}
Write-Ok "使用 $python"
Write-Ok ("版本 " + (& $python --version 2>&1))

Write-Step "检查依赖"
& $python -c "import fastapi, uvicorn, sqlalchemy, jwt, reportlab" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Warn "缺少依赖，正在安装 requirements.txt …"
    & $python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "依赖安装失败，请检查网络后重试。"
        exit 1
    }
}
Write-Ok "依赖就绪"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Yellow
Write-Host "  NeuroArchAI Platform 正在启动" -ForegroundColor Yellow
Write-Host "  浏览器打开： http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "  停止服务：   按 Ctrl + C" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Yellow
Write-Host ""

& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000