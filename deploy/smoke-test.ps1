#requires -Version 5.1
<#
.SYNOPSIS
  Post-deploy smoke test for a local compose stack or a hosted deployment.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\deploy\smoke-test.ps1 -ApiUrl http://localhost:3001 -FrontendUrl http://localhost:3000
#>
[CmdletBinding()]
param(
  [string]$ApiUrl = "http://localhost:3001",
  [string]$FrontendUrl = "http://localhost:3000",
  [string]$ApiKey = "",
  [string]$ScanDirectory = "/workspace/projects/backend/src",
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = "Stop"
$failed = 0

function Read-DotEnv([string]$Path) {
  $map = @{}
  if (-not (Test-Path -LiteralPath $Path)) { return $map }
  foreach ($line in Get-Content -LiteralPath $Path) {
    if ($line -match '^\s*#' -or $line -match '^\s*$') { continue }
    $idx = $line.IndexOf('=')
    if ($idx -lt 1) { continue }
    $map[$line.Substring(0, $idx).Trim()] = $line.Substring($idx + 1).Trim()
  }
  return $map
}

if ([string]::IsNullOrWhiteSpace($ApiKey)) {
  $envMap = Read-DotEnv (Join-Path $RepoRoot ".env")
  $ApiKey = $envMap["QTRUST_API_KEY"]
  if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    $ApiKey = ($envMap["QTRUST_API_KEYS"] -split ',')[0]
  }
}

function Pass([string]$Name) { Write-Host "PASS  $Name" -ForegroundColor Green }
function Fail([string]$Name, [string]$Detail) {
  Write-Host "FAIL  $Name - $Detail" -ForegroundColor Red
  $script:failed++
}

Write-Host "==> API health: $ApiUrl/health"
try {
  $health = Invoke-RestMethod -Uri "$ApiUrl/health" -TimeoutSec 30
  if ($health.status -eq "ok") { Pass "api /health (chain $($health.chain_id), relayer $($health.relayer))" }
  else { Fail "api /health" "unexpected payload: $($health | ConvertTo-Json -Compress)" }
} catch { Fail "api /health" $_.Exception.Message }

if (-not [string]::IsNullOrWhiteSpace($ApiKey)) {
  Write-Host "==> API docs (authenticated)"
  try {
    $headers = @{ "x-api-key" = $ApiKey }
    $null = Invoke-RestMethod -Uri "$ApiUrl/docs/json" -Headers $headers -TimeoutSec 30
    Pass "api /docs/json with x-api-key"
  } catch { Fail "api /docs/json" $_.Exception.Message }

  Write-Host "==> Planner proxied endpoint"
  try {
    $headers = @{ "x-api-key" = $ApiKey }
    $planner = Invoke-RestMethod -Uri "$ApiUrl/v1/plans/health" -Headers $headers -TimeoutSec 60
    Pass "api -> planner ($($planner.status))"
  } catch { Fail "api /v1/plans/health" $_.Exception.Message }

  Write-Host "==> Scanner: $ScanDirectory"
  try {
    $body = @{ directory = $ScanDirectory } | ConvertTo-Json -Compress
    $scan = Invoke-RestMethod -Method POST -Uri "$ApiUrl/v1/scan/source" `
      -Headers @{ "x-api-key" = $ApiKey; "content-type" = "application/json" } `
      -Body $body -TimeoutSec 120
    $count = @($scan.findings).Count
    Pass "scan source ($count findings)"
  } catch { Fail "scan source" $_.Exception.Message }
}

Write-Host "==> Frontend: $FrontendUrl/"
try {
  $page = Invoke-WebRequest -Uri "$FrontendUrl/" -TimeoutSec 60 -UseBasicParsing
  if ($page.StatusCode -eq 200) { Pass "frontend HTTP 200" } else { Fail "frontend" "HTTP $($page.StatusCode)" }
} catch { Fail "frontend" $_.Exception.Message }

if ($failed -eq 0) {
  Write-Host ""
  Write-Host "ALL SMOKE CHECKS PASSED" -ForegroundColor Green
  exit 0
}
Write-Host ""
Write-Host "$failed CHECK(S) FAILED" -ForegroundColor Red
exit 1
