# Git repository health check

param([switch]$Verbose)

Write-Host "Git Check – $(Get-Date -Format o)" -ForegroundColor Cyan

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "git is not installed or not on PATH." -ForegroundColor Red
    exit 1
}

$root = git rev-parse --show-toplevel 2>$null
if (-not $root) {
    Write-Host "Not inside a git repository." -ForegroundColor Yellow
    exit 2
}

Write-Host "Repo root : $root"
Write-Host "Branch    : $(git branch --show-current)"
Write-Host "Status    :"
git status -sb
Write-Host ""
Write-Host "Recent commits:"
git log -5 --oneline
Write-Host "Status  : OK" -ForegroundColor Green
exit 0
