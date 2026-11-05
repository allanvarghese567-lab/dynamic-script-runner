# AWS connectivity / identity quick check
# Requires AWS CLI to be installed and configured.

param([switch]$Verbose)

Write-Host "AWS Check – $(Get-Date -Format o)" -ForegroundColor Cyan

try {
    $identity = aws sts get-caller-identity 2>&1 | ConvertFrom-Json
    Write-Host "Account : $($identity.Account)"
    Write-Host "UserId  : $($identity.UserId)"
    Write-Host "ARN     : $($identity.Arn)"
    Write-Host "Status  : OK" -ForegroundColor Green
    exit 0
} catch {
    Write-Host "AWS CLI not available or not configured." -ForegroundColor Yellow
    Write-Host $_.Exception.Message
    exit 1
}
