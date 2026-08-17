[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Demo,

    [Parameter()]
    [string]$OutputRoot = 'results\regression',

    [Parameter()]
    [int]$MaxMiB = 2048
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-Checked {
    param(
        [Parameter(Mandatory)][string]$Executable,
        [Parameter(Mandatory)][string[]]$Arguments,
        [Parameter(Mandatory)][string]$Description
    )

    Write-Host "==> $Description" -ForegroundColor Cyan
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$venvPython = Join-Path $repositoryRoot '.venv\Scripts\python.exe'
$venvCli = Join-Path $repositoryRoot '.venv\Scripts\iy-analyze.exe'
if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf) -or
    -not (Test-Path -LiteralPath $venvCli -PathType Leaf)) {
    throw 'V1 environment is not ready. Run tools\dev\Setup-V1.ps1 first.'
}
if (-not (Test-Path -LiteralPath $Demo -PathType Leaf)) {
    throw "Demo does not exist: $Demo"
}
$demoPath = (Resolve-Path -LiteralPath $Demo).Path
if ($demoPath -notmatch '(?i)\.dem(?:\.zst|\.bz2)?$') {
    throw "Unsupported demo extension: $demoPath"
}
if ($MaxMiB -le 0) {
    throw 'MaxMiB must be positive.'
}

$sourceHash = (Get-FileHash -LiteralPath $demoPath -Algorithm SHA256).Hash.ToLowerInvariant()
$resolvedOutputRoot = if ([IO.Path]::IsPathRooted($OutputRoot)) {
    $OutputRoot
} else {
    Join-Path $repositoryRoot $OutputRoot
}
$runOutput = Join-Path $resolvedOutputRoot $sourceHash.Substring(0, 12)
New-Item -ItemType Directory -Path $runOutput -Force | Out-Null

Invoke-Checked -Executable $venvCli -Arguments @($demoPath, '--output', $runOutput, '--max-mib', [string]$MaxMiB) -Description 'Analyze representative demo'
$analysisPath = Join-Path $runOutput "$($sourceHash.Substring(0, 12)).analysis.json"
if (-not (Test-Path -LiteralPath $analysisPath -PathType Leaf)) {
    throw "Expected analysis output is missing: $analysisPath"
}
Invoke-Checked -Executable $venvPython -Arguments @('-m', 'improve_yourself.validation', $analysisPath) -Description 'Validate iy.analysis/v1 contract and invariants'

$analysis = Get-Content -LiteralPath $analysisPath -Raw | ConvertFrom-Json
$summary = [ordered]@{
    schema = $analysis.schema
    source_sha256 = $analysis.source_sha256
    map_name = $analysis.map_name
    tickrate = $analysis.tickrate
    kill_count = @($analysis.kills).Count
    multikill_count = @($analysis.multikills).Count
    data_quality_status = $analysis.data_quality.status
    available_channels = @($analysis.available_channels)
    missing_channels = @($analysis.data_quality.missing_channels)
    warning_count = @($analysis.data_quality.warnings).Count
}
$summaryPath = Join-Path $runOutput 'regression-summary.json'
$summary | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $summaryPath -Encoding utf8

Write-Host 'PASS: Representative demo regression completed.' -ForegroundColor Green
Write-Host "Analysis: $analysisPath"
Write-Host "Summary:  $summaryPath"
