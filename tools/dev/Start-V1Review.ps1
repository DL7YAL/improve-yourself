[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Demo,

    [Parameter()]
    [string]$OutputRoot = 'results\workflow',

    [Parameter()]
    [string]$Radar,

    [Parameter()]
    [double]$PosX = 0,

    [Parameter()]
    [double]$PosY = 0,

    [Parameter()]
    [double]$Scale = 1,

    [Parameter()]
    [ValidateRange(1, 65535)]
    [int]$Port = 8765,

    [Parameter()]
    [ValidateRange(1, 8192)]
    [int]$MaxMiB = 2048,

    [Parameter()]
    [ValidateRange(1, 4096)]
    [int]$MaxFrames = 256,

    [Parameter()]
    [switch]$SkipSetup,

    [Parameter()]
    [switch]$NoServe
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$setupScript = Join-Path $PSScriptRoot 'Setup-V1.ps1'
$analyzerCli = Join-Path $repositoryRoot '.venv\Scripts\iy-analyzer-server.exe'

if (-not (Test-Path -LiteralPath $Demo -PathType Leaf)) {
    throw "Demo does not exist: $Demo"
}
$demoPath = (Resolve-Path -LiteralPath $Demo).Path
if ($Radar) {
    if (-not (Test-Path -LiteralPath $Radar -PathType Leaf)) {
        throw "Radar does not exist: $Radar"
    }
    if ($Scale -le 0) {
        throw 'Scale must be positive when a radar is supplied.'
    }
    $radarPath = (Resolve-Path -LiteralPath $Radar).Path
}

Push-Location $repositoryRoot
try {
    if (-not $SkipSetup) {
        Write-Host '==> Prepare locked Python 3.13 baseline' -ForegroundColor Cyan
        & $setupScript -SkipTests
        if ($LASTEXITCODE -ne 0) {
            throw "Setup failed with exit code $LASTEXITCODE."
        }
    }

    foreach ($entryPoint in @($analyzerCli)) {
        if (-not (Test-Path -LiteralPath $entryPoint -PathType Leaf)) {
            throw "Required entry point is missing: $entryPoint. Run without -SkipSetup."
        }
    }

    $analyzerArguments = @(
        $demoPath, '--output', $OutputRoot,
        '--max-mib', [string]$MaxMiB,
        '--max-frames', [string]$MaxFrames,
        '--port', [string]$Port
    )
    if ($Radar) {
        $analyzerArguments += @(
            '--radar', $radarPath,
            '--pos-x', $PosX.ToString([Globalization.CultureInfo]::InvariantCulture),
            '--pos-y', $PosY.ToString([Globalization.CultureInfo]::InvariantCulture),
            '--scale', $Scale.ToString([Globalization.CultureInfo]::InvariantCulture)
        )
    }

    if ($NoServe) { throw 'NoServe is no longer supported for the interactive preflight; use iy-workflow for non-interactive artifact generation.' }
    Write-Host '==> Start local Analyzer V1 preflight' -ForegroundColor Cyan
    & $analyzerCli @analyzerArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Analyzer service failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
