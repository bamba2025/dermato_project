param([switch]$NativeAndroid)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$nodeDirectory = Join-Path $projectRoot '.tools/node-v22.20.0-win-x64'
if (Test-Path -LiteralPath (Join-Path $nodeDirectory 'node.exe')) {
    $env:Path = "$nodeDirectory;" + $env:Path
}
$pythonExe = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { $pythonExe = 'python' }
function Invoke-Check([string]$checkExe, [string[]]$checkArguments) {
    & $checkExe @checkArguments
    if ($LASTEXITCODE -ne 0) { throw "Contrôle échoué : $checkExe $checkArguments" }
}
Push-Location -LiteralPath $projectRoot
try {
    Invoke-Check $pythonExe @('-m', 'ruff', 'check', 'backend/app', 'backend/migrations', 'backend/tests', 'worker', 'scripts')
    Invoke-Check $pythonExe @('-m', 'ruff', 'format', '--check', 'backend/app', 'backend/migrations', 'backend/tests', 'worker', 'scripts')
    Invoke-Check $pythonExe @('-m', 'mypy', '--config-file', 'backend/pyproject.toml', 'backend/app')
    Push-Location -LiteralPath (Join-Path $projectRoot 'backend')
    try { Invoke-Check $pythonExe @('-m', 'pytest', '-q') }
    finally { Pop-Location }
    Push-Location -LiteralPath (Join-Path $projectRoot 'mobile')
    try {
        Invoke-Check 'npm.cmd' @('run', 'typecheck')
        Invoke-Check 'npm.cmd' @('run', 'lint')
        Invoke-Check 'npm.cmd' @('test', '--', '--runInBand')
        Invoke-Check 'npm.cmd' @('run', 'bundle:android')
        Invoke-Check 'npm.cmd' @('run', 'bundle:ios')
        if ($NativeAndroid) {
            Push-Location -LiteralPath (Join-Path $projectRoot 'mobile/android')
            try { Invoke-Check '.\gradlew.bat' @(':app:assembleDebug', '--no-daemon') }
            finally { Pop-Location }
        }
    } finally { Pop-Location }
    Write-Host 'Contrôles du code OK. Compose et les compilations natives sont des validations distinctes.'
} finally { Pop-Location }
