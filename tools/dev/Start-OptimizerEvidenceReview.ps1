[CmdletBinding()]
param([Parameter()][string]$OutputRoot = 'results\optimizer-evidence-review',[switch]$Offline)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$system=Join-Path $root '.venv\Scripts\iy-system-check.exe'
$review=Join-Path $root '.venv\Scripts\iy-optimizer-evidence-review.exe'
$out=(Join-Path $root $OutputRoot); New-Item -ItemType Directory -Force -Path $out | Out-Null
Write-Host $(if($Offline){'==> Collect offline local read-only System Check evidence'}else{'==> Collect local read-only System Check evidence'}) -ForegroundColor Cyan
& $system '--output' (Join-Path $out 'system-check.json') $(if($Offline){'--offline'}); if($LASTEXITCODE -ne 0){throw "System Check failed: $LASTEXITCODE"}
Write-Host '==> Render local read-only Optimizer Evidence review' -ForegroundColor Cyan
& $review (Join-Path $out 'system-check.json') '--output' (Join-Path $out 'optimizer-evidence-review.html'); if($LASTEXITCODE -ne 0){throw "Evidence review failed: $LASTEXITCODE"}
Write-Host "READY: Open $(Join-Path $out 'optimizer-evidence-review.html')" -ForegroundColor Green
