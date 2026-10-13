param(
    [string]$ConfigPath = (Join-Path (Split-Path -Parent $PSScriptRoot) 'private/local-aws.json')
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $ConfigPath)) {
    throw 'Falta private/local-aws.json; genera la configuración local antes de usar AWS.'
}

$config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
if (-not $config.profile -or -not $config.region -or -not $config.account_id -or -not $config.principal_arn) {
    throw 'Configuración AWS local incompleta.'
}

$configuredRegion = & aws configure get region --profile $config.profile
if ($LASTEXITCODE -ne 0 -or $configuredRegion.Trim() -ne $config.region) {
    throw 'La región AWS configurada no coincide con la aprobada localmente.'
}

$identityJson = & aws sts get-caller-identity --profile $config.profile --region $config.region --output json
if ($LASTEXITCODE -ne 0) {
    throw 'No fue posible comprobar la identidad AWS.'
}
$identity = $identityJson | ConvertFrom-Json
if ($identity.Account -ne $config.account_id -or $identity.Arn -ne $config.principal_arn) {
    throw 'La cuenta o el principal AWS no coinciden con la configuración local.'
}

$lastFour = $identity.Account.Substring($identity.Account.Length - 4)
Write-Output "Identidad AWS verificada: cuenta ****$lastFour, perfil $($config.profile), región $($config.region)."
