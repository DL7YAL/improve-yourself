[CmdletBinding()]
param(
    [string]$WorkspacePath = (Join-Path $env:USERPROFILE "Documents\Codex\improve-yourself"),
    [string]$Repository = "git@github.com:DL7YAL/improve-yourself.git",
    [string]$Branch = "main",
    [string]$GitUserName = "DL7YAL",
    [string]$GitUserEmail = "DL7YAL@users.noreply.github.com"
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([Parameter(Mandatory)][string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name wurde nicht gefunden. Bitte Git for Windows (einschliesslich OpenSSH) installieren."
    }
}

Require-Command git
Require-Command ssh-keygen

$sshDirectory = Join-Path $env:USERPROFILE ".ssh"
$keyPath = Join-Path $sshDirectory "id_ed25519_github"
$publicKeyPath = "$keyPath.pub"

New-Item -ItemType Directory -Path $sshDirectory -Force | Out-Null

if (-not (Test-Path -LiteralPath $publicKeyPath)) {
    Write-Host "Ein neuer GitHub-SSH-Schluessel wird erstellt."
    ssh-keygen -t ed25519 -a 100 -f $keyPath -C "$GitUserName GitHub"
    Write-Host ""
    Write-Host "Den folgenden OEFFENTLICHEN Schluessel jetzt in GitHub unter Settings > SSH and GPG keys > New SSH key hinterlegen:"
    Get-Content -LiteralPath $publicKeyPath
    Write-Host ""
    throw "Schluessel in GitHub hinterlegen und dieses Skript danach erneut ausfuehren. Der private Schluessel bleibt lokal."
}

$parentPath = Split-Path -Parent $WorkspacePath
New-Item -ItemType Directory -Path $parentPath -Force | Out-Null
$sshCommand = "ssh -i `"$keyPath`" -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
$previousGitSshCommand = $env:GIT_SSH_COMMAND
$env:GIT_SSH_COMMAND = $sshCommand

try {
    if (Test-Path -LiteralPath $WorkspacePath) {
        $entries = Get-ChildItem -LiteralPath $WorkspacePath -Force
        if ($entries.Count -gt 0 -and -not (Test-Path -LiteralPath (Join-Path $WorkspacePath ".git"))) {
            throw "Zielordner ist nicht leer und kein Git-Repository: $WorkspacePath. Abbruch, um vorhandene Daten zu schuetzen."
        }
    }

    if (-not (Test-Path -LiteralPath (Join-Path $WorkspacePath ".git"))) {
        git clone --branch $Branch $Repository $WorkspacePath
    }

    Push-Location $WorkspacePath
    try {
        git remote set-url origin $Repository
        git config core.sshCommand $sshCommand
        git config user.name $GitUserName
        git config user.email $GitUserEmail
        git fetch origin
        git checkout $Branch
        git pull --ff-only origin $Branch
        git status --short --branch
    }
    finally {
        Pop-Location
    }
}
finally {
    if ($null -eq $previousGitSshCommand) {
        Remove-Item Env:GIT_SSH_COMMAND -ErrorAction SilentlyContinue
    }
    else {
        $env:GIT_SSH_COMMAND = $previousGitSshCommand
    }
}

Write-Host "Lokaler GitHub-Arbeitsordner ist eingerichtet: $WorkspacePath"
