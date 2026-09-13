[CmdletBinding()]
param(
    [string]$Repo = (Join-Path $env:USERPROFILE 'Documents\ChatGPT\BRIX1')
)
$ErrorActionPreference = 'Stop'
$pythonExe = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'
$env:PATH = (Join-Path $env:ProgramFiles 'Git\cmd') + ';' + $env:PATH
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Push-Location $root
try {
    & $pythonExe -m unittest discover -s tests -p test_work_bridge.py -v
    if ($LASTEXITCODE -ne 0) { throw 'Windows tests failed; schedule not installed.' }
    # Parse every supplied PowerShell script before installation.
    foreach ($file in @('Work-Bridge.ps1','Install-WorkBridgeSchedule.ps1','Run-WorkBridgeScheduled.ps1')) {
        $tokens = $null; $errors = $null
        [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot $file), [ref]$tokens, [ref]$errors) | Out-Null
        if ($errors.Count -gt 0) { throw ('PowerShell parse failed: ' + $file) }
    }
    & (Join-Path $PSHOME 'powershell.exe') -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'Work-Bridge.ps1') -Action status -Repo $Repo -PythonExe $pythonExe
    if ($LASTEXITCODE -ne 0) { throw 'PowerShell wrapper test failed; schedule not installed.' }
    & (Join-Path $PSScriptRoot 'Install-WorkBridgeSchedule.ps1') -Repo $Repo -PythonExe $pythonExe
    Start-Sleep -Seconds 5
    Get-ScheduledTaskInfo -TaskName 'ImproveYourself-WorkBridge-30min' | Format-List LastRunTime,LastTaskResult,NextRunTime
    Write-Host 'Check latest-result.json at the printed runtime path. IDLE means no session is active yet.'
    Write-Host 'BRIX1 has not been switched, committed, or merged by this setup.'
} finally { Pop-Location }
