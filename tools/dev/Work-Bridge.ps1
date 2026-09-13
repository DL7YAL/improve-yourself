[CmdletBinding()]
param(
    [ValidateSet('start','status','checkpoint','auto-checkpoint','finish')]
    [string]$Action = 'status',
    [string]$Repo = '.',
    [string]$BackupRoot,
    [string]$Owner,
    [string]$Session,
    [string]$ReviewedHead,
    [string]$Validation,
    [string]$Handoff,
    [string]$PythonExe = 'python'
)
$ErrorActionPreference = 'Stop'
$arguments = @((Join-Path $PSScriptRoot 'work_bridge.py'), $Action, '--repo', $Repo)
$values = @{
    'backup-root'=$BackupRoot; 'owner'=$Owner; 'session'=$Session
    'reviewed-head'=$ReviewedHead; 'validation'=$Validation; 'handoff'=$Handoff
}
foreach ($key in $values.Keys) {
    if ($values[$key]) { $arguments += @('--' + $key, $values[$key]) }
}
& $PythonExe @arguments
exit $LASTEXITCODE
