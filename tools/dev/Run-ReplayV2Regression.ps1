[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Demo,
    [Parameter(Mandatory)][string]$Analysis,
    [Parameter()][string]$OutputRoot = 'results\replay-v2'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$python = Join-Path $repositoryRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw 'V1 environment is not ready. Run tools\dev\Setup-V1.ps1 first.'
}
if (-not (Test-Path -LiteralPath $Demo -PathType Leaf)) {
    throw "Demo does not exist: $Demo"
}
if (-not (Test-Path -LiteralPath $Analysis -PathType Leaf)) {
    throw "Analysis does not exist: $Analysis"
}

$demoPath = (Resolve-Path -LiteralPath $Demo).Path
$analysisPath = (Resolve-Path -LiteralPath $Analysis).Path
$resolvedOutput = if ([IO.Path]::IsPathRooted($OutputRoot)) { $OutputRoot } else { Join-Path $repositoryRoot $OutputRoot }
$sourceHash = (Get-FileHash -LiteralPath $demoPath -Algorithm SHA256).Hash.ToLowerInvariant()

Write-Host '==> Build canonical iy.replay/v2 store' -ForegroundColor Cyan
& $python -m improve_yourself.replay_builder $demoPath $analysisPath --output $resolvedOutput
if ($LASTEXITCODE -ne 0) { throw "Replay V2 build failed with exit code $LASTEXITCODE." }

$manifest = Join-Path (Join-Path $resolvedOutput $sourceHash.Substring(0, 12)) 'replay-v2.json'
$summary = Join-Path (Split-Path -Parent $manifest) 'regression-summary.json'
Write-Host '==> Validate every manifest and round-chunk invariant' -ForegroundColor Cyan
& $python -m improve_yourself.replay_store $manifest --summary $summary
if ($LASTEXITCODE -ne 0) { throw "Replay V2 validation failed with exit code $LASTEXITCODE." }

Write-Host 'PASS: iy.replay/v2 full-match regression completed.' -ForegroundColor Green
Write-Host "Manifest: $manifest"
Write-Host "Summary:  $summary"
