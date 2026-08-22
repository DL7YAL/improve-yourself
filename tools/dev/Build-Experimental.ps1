[CmdletBinding()]
param(
    [Parameter()]
    [string]$OutputRoot = 'dist\experimental',

    [Parameter()]
    [switch]$SkipTests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-PortableSha256 {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)

    $stream = [System.IO.File]::OpenRead($LiteralPath)
    try {
        $hasher = [System.Security.Cryptography.SHA256]::Create()
        try {
            return ([System.BitConverter]::ToString($hasher.ComputeHash($stream))).Replace('-', '')
        }
        finally {
            $hasher.Dispose()
        }
    }
    finally {
        $stream.Dispose()
    }
}

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$python = Join-Path $repositoryRoot '.venv\Scripts\python.exe'
$spec = Join-Path $repositoryRoot 'packaging\improve-yourself-experimental.spec'
$buildLock = Join-Path $repositoryRoot 'requirements-build.lock'
$output = Join-Path $repositoryRoot $OutputRoot
$work = Join-Path $repositoryRoot 'build\pyinstaller-experimental'

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw 'Locked development environment is missing. Run tools/dev/Setup-V1.ps1 first.'
}

Push-Location $repositoryRoot
try {
    if (-not $SkipTests) {
        & $python -m pytest
        if ($LASTEXITCODE -ne 0) { throw "Tests failed with exit code $LASTEXITCODE." }
    }
    & $python -m pip install -r $buildLock
    if ($LASTEXITCODE -ne 0) { throw "Build dependency setup failed with exit code $LASTEXITCODE." }
    & $python -m pip check
    if ($LASTEXITCODE -ne 0) { throw "Dependency check failed with exit code $LASTEXITCODE." }
    & $python -m PyInstaller --noconfirm --clean --distpath $output --workpath $work $spec
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE." }

    $portable = Join-Path $output 'Improve Yourself'
    $executable = Join-Path $portable 'Improve Yourself.exe'
    $testerReadme = Join-Path $repositoryRoot 'packaging\EXTERNAL_TEST_CANDIDATE_README.txt'
    $testerReadmeTarget = Join-Path $portable 'EXTERNAL_TEST_CANDIDATE_README.txt'
    if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
        throw "Portable executable is missing: $executable"
    }
    if (-not (Test-Path -LiteralPath $testerReadme -PathType Leaf)) {
        throw "External tester readme is missing: $testerReadme"
    }
    Copy-Item -LiteralPath $testerReadme -Destination $testerReadmeTarget -Force
    if (-not (Test-Path -LiteralPath $testerReadmeTarget -PathType Leaf)) {
        throw "External tester readme was not staged: $testerReadmeTarget"
    }
    $zip = Join-Path $output 'Improve-Yourself-Experimental-Portable.zip'
    Compress-Archive -LiteralPath $portable -DestinationPath $zip -CompressionLevel Optimal -Force
    $executableHash = Get-PortableSha256 -LiteralPath $executable
    $zipHash = Get-PortableSha256 -LiteralPath $zip
    $manifest = [ordered]@{
        schema = 'iy.experimental_build/v1'
        channel = 'experimental'
        distribution = 'portable'
        tests_skipped = [bool]$SkipTests
        executable = [ordered]@{ path = 'Improve Yourself\Improve Yourself.exe'; sha256 = $executableHash; bytes = (Get-Item -LiteralPath $executable).Length }
        archive = [ordered]@{ path = 'Improve-Yourself-Experimental-Portable.zip'; sha256 = $zipHash; bytes = (Get-Item -LiteralPath $zip).Length }
    }
    $manifestPath = Join-Path $output 'experimental-build.json'
    $manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestPath -Encoding utf8
    [pscustomobject]@{ Path = $executable; SHA256 = $executableHash }, [pscustomobject]@{ Path = $zip; SHA256 = $zipHash }
    Write-Host 'PASS: Experimental portable build is ready.' -ForegroundColor Green
    Write-Host "Portable: $portable"
    Write-Host "Archive:  $zip"
    Write-Host "Manifest: $manifestPath"
    Write-Host 'Setup:    not generated; no supported installer toolchain is currently defined.'
}
finally {
    Pop-Location
}
