<#
.SYNOPSIS
    本地 Docker 构建与运行校验脚本。

.DESCRIPTION
    依次执行：校验 docker-compose.yml -> 构建镜像 -> 启动容器 -> 健康检查。
    需要本机已安装 Docker Desktop。

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\verify_docker.ps1
#>

$ErrorActionPreference = "Stop"

function Write-Step($text) { Write-Host "==> $text" -ForegroundColor Cyan }
function Write-Ok($text) { Write-Host "    $text" -ForegroundColor Green }
function Write-Fail($text) { Write-Host "    $text" -ForegroundColor Red }

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Fail "未检测到 docker 命令。"
    Write-Host "请先安装 Docker Desktop：https://www.docker.com/products/docker-desktop/"
    exit 1
}

Write-Step "0/3 检查 Docker 是否在运行"
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Fail "Docker 已安装但未启动，请先打开 Docker Desktop 并等待其就绪。"
    exit 1
}
Write-Ok "Docker 可用"

Write-Step "1/3 校验 docker-compose.yml"
docker compose config *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Fail "compose 配置校验未通过"
    exit 1
}
Write-Ok "compose 配置正确"

Write-Step "2/3 构建镜像（多阶段：Node 构建前端 + Python 运行）"
docker build -t neuroarchai-platform:local .
if ($LASTEXITCODE -ne 0) {
    Write-Fail "镜像构建失败"
    exit 1
}
Write-Ok "镜像构建成功"

Write-Step "3/3 启动容器并健康检查"
docker compose up -d
Start-Sleep -Seconds 10
try {
    $health = Invoke-RestMethod "http://127.0.0.1:8000/api/health" -TimeoutSec 10
    Write-Ok ("健康检查通过：" + ($health | ConvertTo-Json -Compress))
    Write-Host ""
    Write-Host "打开 http://127.0.0.1:8000 查看界面" -ForegroundColor Yellow
    Write-Host "停止：docker compose down" -ForegroundColor Yellow
} catch {
    Write-Fail "健康检查失败，下面是最近 40 行容器日志："
    docker compose logs --tail 40
    exit 1
}
