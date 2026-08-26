[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Demo,
    [Parameter()][string]$OutputRoot = 'results\demo-workflow',
    [Parameter()][ValidateRange(1, 65535)][int]$Port = 8766,
    [Parameter()][ValidateRange(1, 8192)][int]$MaxMiB = 2048,
    [Parameter()][switch]$SkipSetup,
    [Parameter()][switch]$NoServe
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$setupScript = Join-Path $PSScriptRoot 'Setup-V1.ps1'
$demoCli = Join-Path $repositoryRoot '.venv\Scripts\iy-demo-workflow.exe'
$reviewCli = Join-Path $repositoryRoot '.venv\Scripts\iy-v2-local-review.exe'

if (-not (Test-Path -LiteralPath $Demo -PathType Leaf)) { throw "Demo does not exist: $Demo" }
$demoPath = (Resolve-Path -LiteralPath $Demo).Path
Push-Location $repositoryRoot
try {
    Write-Host '==> Improve Yourself: local V2 review' -ForegroundColor Cyan
    Write-Host "    Demo:   $demoPath"
    Write-Host "    Output: $OutputRoot (stable folder per demo SHA-256)"
    if (-not $SkipSetup) { Write-Host '==> Prepare locked Python 3.13 baseline' -ForegroundColor Cyan; & $setupScript -SkipTests; if ($LASTEXITCODE -ne 0) { throw "Setup failed with exit code $LASTEXITCODE." } }
    foreach ($entryPoint in @($demoCli, $reviewCli)) { if (-not (Test-Path -LiteralPath $entryPoint -PathType Leaf)) { throw "Required entry point is missing: $entryPoint. Run without -SkipSetup." } }
    Write-Host '==> Analyze selected local demo and build canonical Replay V2' -ForegroundColor Cyan
    $workflowOutput = @(& $demoCli $demoPath '--output' $OutputRoot '--max-mib' ([string]$MaxMiB))
    if ($LASTEXITCODE -ne 0) { throw "V2 workflow failed with exit code $LASTEXITCODE." }
    $manifestText = @($workflowOutput | Where-Object { $_ -and $_.Trim() })[-1]
    if (-not $manifestText -or -not (Test-Path -LiteralPath $manifestText -PathType Leaf)) { throw 'V2 workflow did not return a valid manifest path.' }
    Write-Host "==> Validate hash-bound workflow: $manifestText" -ForegroundColor Cyan
    if ($NoServe) { Write-Host '==> Prepare review artifacts without starting a server' -ForegroundColor Cyan; & $reviewCli $manifestText '--prepare-only'; if ($LASTEXITCODE -ne 0) { throw "V2 review preparation failed with exit code $LASTEXITCODE." }; Write-Host 'READY: Open the printed review.html locally, or rerun without -NoServe for loopback serving.' -ForegroundColor Green; return }
    Write-Host "==> Start local review at http://127.0.0.1:$Port/review.html" -ForegroundColor Green
    & $reviewCli $manifestText '--port' ([string]$Port)
    if ($LASTEXITCODE -ne 0) { throw "V2 review server failed with exit code $LASTEXITCODE." }
}
finally { Pop-Location }
