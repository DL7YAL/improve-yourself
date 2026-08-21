[CmdletBinding()]
param(
    [Parameter()]
    [string]$Workflow,

    [Parameter()]
    [string]$OutputRoot = 'results\analyzer-shell',

    [Parameter()]
    [switch]$SkipSetup
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$setupScript = Join-Path $PSScriptRoot 'Setup-V1.ps1'
$shellCli = Join-Path $repositoryRoot '.venv\Scripts\iy-analyzer-shell.exe'
$arguments = @('--output', $OutputRoot)

if ($Workflow) {
    if (-not (Test-Path -LiteralPath $Workflow -PathType Leaf)) {
        throw "Workflow does not exist: $Workflow"
    }
    $workflowPath = (Resolve-Path -LiteralPath $Workflow).Path
    if ([IO.Path]::GetFileName($workflowPath) -ne 'demo-workflow.json') {
        throw 'Workflow must be an explicitly selected demo-workflow.json file.'
    }
    $arguments += @('--workflow', $workflowPath)
}

Push-Location $repositoryRoot
try {
    if (-not $SkipSetup) {
        Write-Host '==> Prepare locked Experimental baseline' -ForegroundColor Cyan
        & $setupScript -SkipTests
        if ($LASTEXITCODE -ne 0) {
            throw "Setup failed with exit code $LASTEXITCODE."
        }
    }

    if (-not (Test-Path -LiteralPath $shellCli -PathType Leaf)) {
        throw "Experimental entry point is missing: $shellCli. Run without -SkipSetup."
    }

    Write-Host '==> Start Improve Yourself - Experimental' -ForegroundColor Cyan
    Write-Host 'Local only; no data is uploaded and no system setting is changed.'
    if ($Workflow) {
        Write-Host "Workflow: $workflowPath"
    }
    & $shellCli @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Experimental shell failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
