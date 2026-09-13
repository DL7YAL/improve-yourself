$ErrorActionPreference = 'Stop'
$code = 1
$output = ''
try {
    $config = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'schedule.json') -Raw | ConvertFrom-Json
    $env:PATH = $config.gitDirectory + ';' + $env:PATH
    $output = (& $config.python (Join-Path $PSScriptRoot 'work_bridge.py') auto-checkpoint --repo $config.repo 2>&1 | Out-String)
    $code = $LASTEXITCODE
} catch { $output = $_.Exception.Message }
@{ timestamp=(Get-Date).ToString('o'); exitCode=$code; output=$output } |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'latest-result.json') -Encoding UTF8
if ($code -ne 0) {
    ((Get-Date).ToString('o') + ' ' + $output) | Add-Content -LiteralPath (Join-Path $PSScriptRoot 'failures.log')
}
exit $code
