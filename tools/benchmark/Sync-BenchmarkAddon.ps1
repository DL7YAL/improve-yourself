[CmdletBinding()]
param(
    [Parameter()]
    [string]$AddonRoot,

    [Parameter()]
    [switch]$Deploy
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Sha256 {
    param([Parameter(Mandatory)][string]$LiteralPath)

    return (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Resolve-DefaultAddonRoot {
    $steam = Get-ItemProperty -Path 'HKCU:\Software\Valve\Steam' -ErrorAction Stop
    if ([string]::IsNullOrWhiteSpace($steam.SteamPath)) {
        throw 'SteamPath is missing from HKCU:\Software\Valve\Steam.'
    }

    return Join-Path $steam.SteamPath 'steamapps\common\Counter-Strike Global Offensive\content\csgo_addons\improve_yourself_benchmark'
}

function Assert-SafeAddonRoot {
    param([Parameter(Mandatory)][string]$LiteralPath)

    if (-not (Test-Path -LiteralPath $LiteralPath -PathType Container)) {
        throw "Addon root does not exist: $LiteralPath"
    }

    $resolved = (Resolve-Path -LiteralPath $LiteralPath).Path
    $item = Get-Item -LiteralPath $resolved -Force
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Addon root must not be a reparse point: $resolved"
    }
    if ($item.Name -ne 'improve_yourself_benchmark') {
        throw "Refusing target whose final directory is not improve_yourself_benchmark: $resolved"
    }
    if ($resolved -notmatch '[\\/]content[\\/]csgo_addons[\\/]improve_yourself_benchmark$') {
        throw "Refusing target outside a CS2 content/csgo_addons directory: $resolved"
    }

    return $resolved
}

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$sourceRoot = Join-Path $repositoryRoot 'assets\maps\improve_yourself_benchmark'
$manifestPath = Join-Path $sourceRoot 'source-manifest.json'

if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Source manifest is missing: $manifestPath"
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.schema -ne 'iy.cs2-addon-sources/v1' -or $manifest.addon -ne 'improve_yourself_benchmark') {
    throw 'Source manifest schema or addon name is invalid.'
}
if ($manifest.files.Count -ne 2) {
    throw "Expected exactly two manifest files; found $($manifest.files.Count)."
}

if ([string]::IsNullOrWhiteSpace($AddonRoot)) {
    $AddonRoot = Resolve-DefaultAddonRoot
}
$targetRoot = Assert-SafeAddonRoot -LiteralPath $AddonRoot

$checks = foreach ($entry in $manifest.files) {
    $relativePath = [string]$entry.path
    if ([string]::IsNullOrWhiteSpace($relativePath) -or
        [IO.Path]::IsPathRooted($relativePath) -or
        $relativePath -match '(^|[\\/])\.\.([\\/]|$)') {
        throw "Unsafe manifest path: $relativePath"
    }

    $nativeRelativePath = $relativePath -replace '/', [IO.Path]::DirectorySeparatorChar
    $sourcePath = Join-Path $sourceRoot $nativeRelativePath
    $targetPath = Join-Path $targetRoot $nativeRelativePath
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
        throw "Manifest source is missing: $sourcePath"
    }

    $expectedHash = ([string]$entry.sha256).ToUpperInvariant()
    $sourceHash = Get-Sha256 -LiteralPath $sourcePath
    if ($sourceHash -ne $expectedHash) {
        throw "Repository source hash does not match manifest for ${relativePath}: expected $expectedHash, got $sourceHash"
    }

    $targetExists = Test-Path -LiteralPath $targetPath -PathType Leaf
    $targetHash = if ($targetExists) { Get-Sha256 -LiteralPath $targetPath } else { $null }

    [pscustomobject]@{
        RelativePath = $relativePath
        SourcePath = $sourcePath
        TargetPath = $targetPath
        ExpectedHash = $expectedHash
        TargetExists = $targetExists
        TargetHash = $targetHash
        Matches = $targetExists -and $targetHash -eq $expectedHash
    }
}

$drift = @($checks | Where-Object { -not $_.Matches })
if (-not $Deploy) {
    $checks | Select-Object RelativePath, TargetExists, TargetHash, ExpectedHash, Matches | Format-Table -AutoSize
    if ($drift.Count -gt 0) {
        Write-Error "Verification found $($drift.Count) missing or different addon source file(s). Re-run with -Deploy to back up and replace only those files."
        exit 2
    }

    Write-Host 'PASS: Installed addon sources match the repository manifest.' -ForegroundColor Green
    exit 0
}

if ($drift.Count -eq 0) {
    Write-Host 'PASS: No deployment needed; installed addon sources already match the repository manifest.' -ForegroundColor Green
    exit 0
}

$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupRoot = Join-Path $targetRoot "backups\deploy-$timestamp"

foreach ($check in $drift) {
    if ($check.TargetExists) {
        $backupPath = Join-Path $backupRoot ($check.RelativePath -replace '/', [IO.Path]::DirectorySeparatorChar)
        $backupDirectory = Split-Path -Parent $backupPath
        New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null
        Copy-Item -LiteralPath $check.TargetPath -Destination $backupPath
        if ((Get-Sha256 -LiteralPath $backupPath) -ne $check.TargetHash) {
            throw "Backup verification failed for $($check.RelativePath). Deployment stopped before overwrite."
        }
    }

    $targetDirectory = Split-Path -Parent $check.TargetPath
    New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
    Copy-Item -LiteralPath $check.SourcePath -Destination $check.TargetPath -Force
    $deployedHash = Get-Sha256 -LiteralPath $check.TargetPath
    if ($deployedHash -ne $check.ExpectedHash) {
        throw "Post-deploy verification failed for $($check.RelativePath): expected $($check.ExpectedHash), got $deployedHash"
    }
}

$checksAfterDeploy = foreach ($entry in $manifest.files) {
    $relativePath = [string]$entry.path
    $nativeRelativePath = $relativePath -replace '/', [IO.Path]::DirectorySeparatorChar
    $targetPath = Join-Path $targetRoot $nativeRelativePath
    $actualHash = Get-Sha256 -LiteralPath $targetPath
    [pscustomobject]@{
        RelativePath = $relativePath
        ExpectedHash = ([string]$entry.sha256).ToUpperInvariant()
        ActualHash = $actualHash
        Matches = $actualHash -eq ([string]$entry.sha256).ToUpperInvariant()
    }
}

$checksAfterDeploy | Format-Table -AutoSize
if (@($checksAfterDeploy | Where-Object { -not $_.Matches }).Count -gt 0) {
    throw 'Deployment completed with a verification mismatch.'
}

Write-Host "PASS: Repository sources deployed and verified. Backup root: $backupRoot" -ForegroundColor Green
