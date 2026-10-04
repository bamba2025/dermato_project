# Runtime portable local au projet, sans installation système.
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$toolsRoot = Join-Path $projectRoot '.tools'
$version = '22.20.0'
$archiveName = "node-v$version-win-x64.zip"
$runtime = Join-Path $toolsRoot "node-v$version-win-x64"
if (Test-Path -LiteralPath (Join-Path $runtime 'node.exe')) {
    Write-Host "Node disponible : $runtime"
    exit 0
}
New-Item -ItemType Directory -Path $toolsRoot -Force | Out-Null
$baseUrl = "https://nodejs.org/dist/v$version"
$archive = Join-Path $toolsRoot $archiveName
$checksums = Join-Path $toolsRoot 'SHASUMS256.txt'
Invoke-WebRequest -UseBasicParsing -Uri "$baseUrl/$archiveName" -OutFile $archive
Invoke-WebRequest -UseBasicParsing -Uri "$baseUrl/SHASUMS256.txt" -OutFile $checksums
$line = Get-Content -LiteralPath $checksums | Where-Object { $_ -match "  $([regex]::Escape($archiveName))$" }
if (-not $line) { throw 'Archive absente du manifeste officiel.' }
$expected = ($line -split '\s+')[0]
$actual = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
if ($expected -ne $actual) { throw 'Checksum Node incorrect : installation interrompue.' }
Expand-Archive -LiteralPath $archive -DestinationPath $toolsRoot
& (Join-Path $runtime 'node.exe') --version
if ($LASTEXITCODE -ne 0) { throw 'Node ne fonctionne pas.' }
