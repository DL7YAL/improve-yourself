[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Demo,

    [Parameter()]
    [string]$OutputRoot = 'results\pipeline',

    [Parameter()]
    [int]$MaxMiB = 2048
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-CheckedScript {
    param(
        [Parameter(Mandatory)][string]$Script,
        [Parameter(Mandatory)][hashtable]$Arguments,
        [Parameter(Mandatory)][string]$Description
    )

    Write-Host "==> $Description" -ForegroundColor Cyan
    & $Script @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$setupScript = Join-Path $PSScriptRoot 'Setup-V1.ps1'
$regressionScript = Join-Path $PSScriptRoot 'Run-DemoRegression.ps1'
if (-not (Test-Path -LiteralPath $Demo -PathType Leaf)) {
    throw "Demo does not exist: $Demo"
}
if ($MaxMiB -le 0) {
    throw 'MaxMiB must be positive.'
}

$demoPath = (Resolve-Path -LiteralPath $Demo).Path
$sourceHash = (Get-FileHash -LiteralPath $demoPath -Algorithm SHA256).Hash.ToLowerInvariant()
$runId = "$(Get-Date -Format 'yyyyMMddTHHmmss')-$($sourceHash.Substring(0, 12))"
$resolvedOutputRoot = if ([IO.Path]::IsPathRooted($OutputRoot)) {
    $OutputRoot
} else {
    Join-Path $repositoryRoot $OutputRoot
}
$runOutput = Join-Path $resolvedOutputRoot $runId
$regressionRoot = Join-Path $runOutput 'regression'
New-Item -ItemType Directory -Path $runOutput -Force | Out-Null

$startedAt = (Get-Date).ToUniversalTime()
$status = 'FAIL'
$failedStep = $null
$baselinePassed = $false
$regressionPassed = $false
try {
    $failedStep = 'baseline'
    Invoke-CheckedScript -Script $setupScript -Arguments @{} -Description 'Verify reproducible V1 baseline'
    $baselinePassed = $true

    $failedStep = 'demo_regression'
    Invoke-CheckedScript -Script $regressionScript -Arguments @{
        Demo = $demoPath
        OutputRoot = $regressionRoot
        MaxMiB = $MaxMiB
    } -Description 'Run representative demo regression'
    $regressionPassed = $true

    $status = 'PASS'
    $failedStep = $null
}
finally {
    $finishedAt = (Get-Date).ToUniversalTime()
    $gitHead = (& git -C $repositoryRoot rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) {
        $gitHead = $null
    }
    $gitStatus = @(& git -C $repositoryRoot status --porcelain)
    if ($LASTEXITCODE -ne 0) {
        $gitStatus = @('git status unavailable')
    }

    $regressionSummaryPath = Join-Path (Join-Path $regressionRoot $sourceHash.Substring(0, 12)) 'regression-summary.json'
    $regression = if (Test-Path -LiteralPath $regressionSummaryPath -PathType Leaf) {
        Get-Content -LiteralPath $regressionSummaryPath -Raw | ConvertFrom-Json
    } else {
        $null
    }
    $evidence = [ordered]@{
        schema = 'iy.pipeline/v1'
        status = $status
        failed_step = $failedStep
        started_at_utc = $startedAt.ToString('o')
        finished_at_utc = $finishedAt.ToString('o')
        duration_seconds = [math]::Round(($finishedAt - $startedAt).TotalSeconds, 3)
        git_head = $gitHead
        git_worktree_clean = @($gitStatus).Count -eq 0
        source_sha256 = $sourceHash
        checks = [ordered]@{
            locked_dependencies = $baselinePassed
            automated_tests = $baselinePassed
            cli_smoke_test = $baselinePassed
            demo_analysis = $regressionPassed -and $null -ne $regression
            analysis_contract = $regressionPassed -and $null -ne $regression
        }
        regression = $regression
    }
    $evidencePath = Join-Path $runOutput 'pipeline-evidence.json'
    $evidence | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $evidencePath -Encoding utf8
    Write-Host "Evidence: $evidencePath"
}

Write-Host 'PASS: V1 pipeline completed.' -ForegroundColor Green
