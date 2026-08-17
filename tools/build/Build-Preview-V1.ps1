[CmdletBinding()]
param([string]$OutputRoot = 'dist\Improve-Yourself-Preview-V1')
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$python = Join-Path $root '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $python)) { throw "Expected project virtual environment: $python" }
if ([IO.Path]::IsPathRooted($OutputRoot)) { $output = $OutputRoot } else { $output = Join-Path $root $OutputRoot }
$resources = Join-Path $root 'build\preview-resources\maps'
New-Item -ItemType Directory -Force -Path $resources | Out-Null
$awpyMaps = Join-Path $env:USERPROFILE '.awpy\maps'
if (!(Test-Path -LiteralPath (Join-Path $awpyMaps 'map-data.json'))) { throw "Required local map metadata is unavailable: $awpyMaps" }
Copy-Item -LiteralPath (Join-Path $awpyMaps 'map-data.json') -Destination $resources -Force
Get-ChildItem -LiteralPath $awpyMaps -Filter '*.png' -File | Copy-Item -Destination $resources -Force
& $python -m PyInstaller --noconfirm --clean --onedir --name 'Improve Yourself' --paths (Join-Path $root 'src') --collect-all awpy --collect-all zstandard --collect-all webview --collect-all clr_loader --collect-all pythonnet --add-data "$resources;resources\maps" --add-data "$(Join-Path $root 'src\improve_yourself\assets');improve_yourself\assets" --distpath $output --workpath (Join-Path $root 'build\pyinstaller') --specpath (Join-Path $root 'build\spec') (Join-Path $root 'src\improve_yourself\preview_launcher.py')
if($LASTEXITCODE -ne 0){throw "PyInstaller failed: $LASTEXITCODE"}
Copy-Item (Join-Path $root 'PREVIEW_V1_README.md') (Join-Path $output 'Improve Yourself\README.md')
