[CmdletBinding()]
param(
    [Parameter()]
    [switch]$SkipTests
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
$venvRoot = Join-Path $repositoryRoot '.venv'
$venvPython = Join-Path $venvRoot 'Scripts\python.exe'
$cliNames = @('iy-analyze', 'iy-system-check', 'iy-workflow', 'iy-replay-viewer', 'iy-review-server', 'iy-analysis-flow', 'iy-demo-workflow')
$lockFile = Join-Path $repositoryRoot 'requirements.lock'

if (-not (Test-Path -LiteralPath $lockFile -PathType Leaf)) {
    throw "Dependency lockfile is missing: $lockFile"
}

Push-Location $repositoryRoot
try {
    if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
        $pyLauncher = Get-Command py -ErrorAction Stop
        Invoke-Checked -Executable $pyLauncher.Source -Arguments @('-3.13', '-m', 'venv', '.venv') -Description 'Create Python 3.13 virtual environment'
    }

    $version = & $venvPython -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to inspect virtual-environment Python at $venvPython."
    }
    if ($version.Trim() -ne '3.13') {
        throw "Existing .venv uses Python $version; Python 3.13 is required. Move or remove it deliberately, then rerun setup."
    }

    Invoke-Checked -Executable $venvPython -Arguments @('-m', 'pip', 'install', '-r', $lockFile) -Description 'Install locked dependencies'
    Invoke-Checked -Executable $venvPython -Arguments @('-m', 'pip', 'install', '--no-deps', '-e', '.') -Description 'Install Improve Yourself in editable mode'
    Invoke-Checked -Executable $venvPython -Arguments @('-m', 'pip', 'check') -Description 'Check dependency consistency'

    if (-not $SkipTests) {
        Invoke-Checked -Executable $venvPython -Arguments @('-m', 'pytest') -Description 'Run automated tests'
    }

    foreach ($cliName in $cliNames) {
        $cliPath = Join-Path $venvRoot "Scripts\$cliName.exe"
        if (-not (Test-Path -LiteralPath $cliPath -PathType Leaf)) {
            throw "CLI entry point is missing after installation: $cliPath"
        }
        Invoke-Checked -Executable $cliPath -Arguments @('--help') -Description "Smoke-test $cliName CLI"
    }

    Write-Host 'PASS: V1 development baseline is ready.' -ForegroundColor Green
    Write-Host "Python: $venvPython"
    Write-Host "CLIs:   $($cliNames -join ', ')"
}
finally {
    Pop-Location
}
