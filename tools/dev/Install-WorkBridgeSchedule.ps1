[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Repo,
    [Parameter(Mandatory=$true)][string]$PythonExe
)
$ErrorActionPreference = 'Stop'
$Repo = (Resolve-Path -LiteralPath $Repo).Path
$PythonExe = (Resolve-Path -LiteralPath $PythonExe).Path
$gitDirectory = Join-Path $env:ProgramFiles 'Git\cmd'
$env:PATH = $gitDirectory + ';' + $env:PATH
$top = & git -C $Repo rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) { throw 'Repository preflight failed.' }
if ((Resolve-Path -LiteralPath $top).Path -ne $Repo) { throw 'Use the checkout root.' }
$taskName = 'ImproveYourself-WorkBridge-30min'
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    throw 'Task already exists. Inspect it before replacing it.'
}
$runtime = Join-Path $env:LOCALAPPDATA ('WorkBridge\' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $runtime | Out-Null
foreach ($file in @('work_bridge.py','Run-WorkBridgeScheduled.ps1')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $file) -Destination $runtime
    if ((Get-FileHash (Join-Path $runtime $file)).Hash -ne (Get-FileHash (Join-Path $PSScriptRoot $file)).Hash) {
        throw 'Runtime copy hash mismatch.'
    }
}
@{ repo=$Repo; python=$PythonExe; gitDirectory=$gitDirectory } |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtime 'schedule.json') -Encoding UTF8
$runner = Join-Path $runtime 'Run-WorkBridgeScheduled.ps1'
$action = New-ScheduledTaskAction -Execute (Join-Path $PSHOME 'powershell.exe') -Argument ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + $runner + '"')
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(30) -RepetitionInterval (New-TimeSpan -Minutes 30)
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 25)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
Write-Host ('Registered ' + $taskName + '; every 30 minutes while logged in.')
Write-Host ('Runtime and result: ' + $runtime)
Write-Host ('Pause: Disable-ScheduledTask -TaskName "' + $taskName + '"')
Start-ScheduledTask -TaskName $taskName
