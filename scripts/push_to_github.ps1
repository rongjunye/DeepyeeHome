<#
.SYNOPSIS
    一键把本项目推送到 GitHub（需已安装 Git）。

.DESCRIPTION
    依次执行：定位 Git -> 初始化仓库（如未初始化）-> 配置提交身份 ->
    暂存全部文件 -> 首次提交 -> 绑定远端 -> 推送。
    推送完成后会打印 GitHub Actions 地址，方便查看 CI 的 Docker 构建结果。

    脚本会自动探测 Git 安装路径，因此即使刚装完 Git、
    当前终端的 PATH 尚未刷新，也能正常工作。

.PARAMETER RepoUrl
    远端仓库地址，例如 https://github.com/你的用户名/NeuroArchAI-Platform.git

.PARAMETER Branch
    分支名，默认 main。

.PARAMETER UserName
    可选：提交者姓名。不传则沿用全局 git 配置。

.PARAMETER UserEmail
    可选：提交者邮箱。不传则沿用全局 git 配置。

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\push_to_github.ps1 `
        -RepoUrl https://github.com/yourname/NeuroArchAI-Platform.git `
        -UserName "Your Name" -UserEmail "you@example.com"
#>

param(
    [Parameter(Mandatory = $true)][string]$RepoUrl,
    [string]$Branch = "main",
    [string]$Message = "chore: initial commit - NeuroArchAI Platform",
    [string]$UserName = "",
    [string]$UserEmail = ""
)

$ErrorActionPreference = "Stop"

function Write-Step($text) { Write-Host "==> $text" -ForegroundColor Cyan }
function Write-Ok($text) { Write-Host "    $text" -ForegroundColor Green }
function Write-Warn($text) { Write-Host "    $text" -ForegroundColor Yellow }
function Write-Fail($text) { Write-Host "    $text" -ForegroundColor Red }

# 定位 Git：优先 PATH，其次常见安装路径（刚装完 Git 时 PATH 可能未刷新）
function Resolve-Git {
    $command = Get-Command git -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }

    $candidates = @(
        "C:\Program Files\Git\cmd\git.exe",
        "C:\Program Files (x86)\Git\cmd\git.exe",
        (Join-Path $env:LOCALAPPDATA "Programs\Git\cmd\git.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

# 0) 依据脚本位置定位仓库根目录
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Step "0/6 定位 Git"
$git = Resolve-Git
if (-not $git) {
    Write-Fail "未找到 git。"
    Write-Host "请先安装 Git for Windows：https://git-scm.com/download/win"
    Write-Host "安装时保持默认选项即可，装完无需重启，重新运行本脚本。"
    exit 1
}
# 把 Git 目录并入 PATH，方便后续子进程调用
$env:Path = (Split-Path -Parent $git) + ";" + $env:Path
Write-Ok "$(& $git --version)  ->  $git"

# 1) 初始化仓库
Write-Step "1/6 初始化仓库"
if (-not (Test-Path ".git")) {
    & $git init -b $Branch 2>$null
    if ($LASTEXITCODE -ne 0) {
        & $git init | Out-Null
        & $git checkout -b $Branch 2>$null | Out-Null
    }
    Write-Ok "已初始化，分支 $Branch"
} else {
    Write-Ok "仓库已存在，跳过初始化"
}

# 2) 提交身份
Write-Step "2/6 检查提交身份"
if ($UserName) { & $git config user.name $UserName }
if ($UserEmail) { & $git config user.email $UserEmail }

$currentName = (& $git config user.name) 2>$null
$currentEmail = (& $git config user.email) 2>$null
if (-not $currentName -or -not $currentEmail) {
    Write-Fail "尚未配置提交身份（user.name / user.email）。"
    Write-Host "可重新运行并追加参数："
    Write-Host '  -UserName "你的名字" -UserEmail "you@example.com"'
    Write-Host "或执行全局配置："
    Write-Host '  git config --global user.name "你的名字"'
    Write-Host '  git config --global user.email "you@example.com"'
    exit 1
}
Write-Ok "$currentName <$currentEmail>"

# 3) 暂存
Write-Step "3/6 暂存文件"
& $git add -A
if ($LASTEXITCODE -ne 0) { Write-Fail "git add 失败"; exit 1 }
$staged = (& $git diff --cached --name-only | Measure-Object -Line).Lines
Write-Ok "已暂存 $staged 个文件"

# 4) 提交
Write-Step "4/6 创建提交"
& $git commit -m $Message | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Warn "没有需要提交的更改，继续下一步"
} else {
    Write-Ok "提交完成"
}

# 5) 绑定远端
Write-Step "5/6 绑定远端"
$existing = (& $git remote get-url origin) 2>$null
if ($existing) {
    & $git remote set-url origin $RepoUrl
    Write-Ok "已更新 origin -> $RepoUrl"
} else {
    & $git remote add origin $RepoUrl
    Write-Ok "已添加 origin -> $RepoUrl"
}

# 6) 推送
Write-Step "6/6 推送到 GitHub"
& $git push -u origin $Branch
if ($LASTEXITCODE -ne 0) {
    Write-Fail "推送失败。常见原因："
    Write-Host "  - 远端仓库并非空仓库（新建时若勾选了 README/.gitignore 会冲突）"
    Write-Host "  - 未完成 Git 凭据登录（首次推送会弹窗，按提示登录 GitHub 即可）"
    Write-Host "  - 网络 / 代理问题"
    exit 1
}
Write-Ok "推送成功"

Write-Host ""
Write-Host "下一步：打开 GitHub 仓库的 Actions 页面查看 CI 结果" -ForegroundColor Yellow
Write-Host "  Docker 构建与容器冒烟测试会在其中自动执行" -ForegroundColor Yellow
Write-Host ("  形如 https://github.com/<你的用户名>/NeuroArchAI-Platform/actions") -ForegroundColor Yellow