param()

$ProjectId = "ksp-suraksha-ai"
$ZipPath = Join-Path $PSScriptRoot "analytics_cron_deploy.zip"
$ApiUrl = "https://api.catalyst.zoho.com/baas/v1/project/$ProjectId/function/upsert"

# Get auth token from CLI
Write-Host "Getting auth token..." -ForegroundColor Cyan
$tokenOutput = & catalyst token:generate --current 2>&1
$token = ($tokenOutput | Select-String "Token generated successfully : (.*)").Matches[0].Groups[1].Value.Trim()
Write-Host "Token acquired: $($token.Substring(0, 20))..." -ForegroundColor Green

# Build the curl command line safely - use cmd /c to avoid PowerShell argument mangling
$cmd = "curl.exe -X PUT"
$cmd += " -H ""Accept: application/vnd.catalyst.v2+json"""
$cmd += " -H ""Authorization: Bearer $token"""
$cmd += " -H ""X-CATALYST-Environment: development"""
$cmd += " -F ""stack=python_3_11"""
$cmd += " -F ""name=analytics_cron"""
$cmd += " -F ""type=basicio"""
$cmd += " -F ""code=@$ZipPath"""
$cmd += " ""$ApiUrl"""

Write-Host "Uploading analytics_cron function..." -ForegroundColor Cyan
$result = cmd /c $cmd 2>&1
$result
