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
$workflowCli = Join-Path $repositoryRoot '.venv\Scripts\iy-workflow.exe'
$reviewCli = Join-Path $repositoryRoot '.venv\Scripts\iy-review-server.exe'

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

    foreach ($entryPoint in @($workflowCli, $reviewCli)) {
        if (-not (Test-Path -LiteralPath $entryPoint -PathType Leaf)) {
            throw "Required entry point is missing: $entryPoint. Run without -SkipSetup."
        }
    }

    $workflowArguments = @(
        $demoPath, '--output', $OutputRoot,
        '--max-mib', [string]$MaxMiB,
        '--max-frames', [string]$MaxFrames
    )
    if ($Radar) {
        $workflowArguments += @(
            '--radar', $radarPath,
            '--pos-x', $PosX.ToString([Globalization.CultureInfo]::InvariantCulture),
            '--pos-y', $PosY.ToString([Globalization.CultureInfo]::InvariantCulture),
            '--scale', $Scale.ToString([Globalization.CultureInfo]::InvariantCulture)
        )
    }

    Write-Host '==> Run local V1 workflow' -ForegroundColor Cyan
    $workflowOutput = @(& $workflowCli @workflowArguments)
    if ($LASTEXITCODE -ne 0) {
        throw "Workflow failed with exit code $LASTEXITCODE."
    }
    $manifestText = @($workflowOutput | Where-Object { $_ -and $_.Trim() })[-1]
    if (-not $manifestText -or -not (Test-Path -LiteralPath $manifestText -PathType Leaf)) {
        throw 'Workflow did not return a valid manifest path.'
    }
    $manifestPath = (Resolve-Path -LiteralPath $manifestText).Path
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    if ($manifest.schema -ne 'iy.workflow/v1' -or $manifest.status -ne 'READY_FOR_REVIEW') {
        throw 'Workflow manifest is not ready for review.'
    }

    $reviewUrl = "http://127.0.0.1:$Port/review.html"
    Write-Host ''
    Write-Host 'READY FOR HUMAN REVIEW' -ForegroundColor Green
    Write-Host "Manifest: $manifestPath"
    Write-Host "Review:   $reviewUrl" -ForegroundColor Cyan
    Write-Host 'Local-only service; no data is uploaded and no system setting was changed.'

    if ($NoServe) {
        Write-Host 'NoServe selected; review service was not started.' -ForegroundColor Yellow
        return
    }

    Write-Host 'Press Ctrl+C to stop the local review service.' -ForegroundColor Yellow
    & $reviewCli $manifestPath --port ([string]$Port)
    if ($LASTEXITCODE -ne 0) {
        throw "Review service failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
