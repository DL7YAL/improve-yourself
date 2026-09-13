[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$BridgeArguments
)
$ErrorActionPreference = 'Stop'
# Use the existing Python installation; no package installation is needed.
& python (Join-Path $PSScriptRoot 'work_bridge.py') @BridgeArguments
exit $LASTEXITCODE
