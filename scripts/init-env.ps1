$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$envTarget = Join-Path $projectRoot '.env'
if (Test-Path -LiteralPath $envTarget) { throw '.env existe déjà : aucune modification.' }
function New-Secret {
    $bytes = New-Object byte[] 32
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    return ([BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
}
$pgSecret = New-Secret
$redisSecret = New-Secret
$storageSecret = New-Secret
$jwtSecret = New-Secret
$seedSecret = New-Secret
$contents = @"
ENVIRONMENT=development
POSTGRES_PASSWORD=$pgSecret
REDIS_PASSWORD=$redisSecret
MINIO_ROOT_USER=derma-local
MINIO_ROOT_PASSWORD=$storageSecret
JWT_SECRET=$jwtSecret
DATABASE_URL=postgresql+psycopg://derma:$pgSecret@postgres:5432/derma
REDIS_URL=redis://:$redisSecret@redis:6379/0
S3_ENDPOINT=http://minio:9000
S3_BUCKET=derma-private
S3_ACCESS_KEY=derma-local
S3_SECRET_KEY=$storageSecret
CORS_ORIGINS=["http://localhost:3000"]
MODEL_BACKBONE=mock
MODEL_PATH=/models
MEDGEMMA_ENABLED=false
GPU_DEVICE=cpu
SEED_PASSWORD=$seedSecret
"@
[IO.File]::WriteAllText($envTarget, $contents, (New-Object Text.UTF8Encoding($false)))
Write-Host '.env créé avec des secrets aléatoires. Aucun secret affiché.'
