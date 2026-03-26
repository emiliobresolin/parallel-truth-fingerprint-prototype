param()

$ErrorActionPreference = "Stop"
$workspace = Resolve-Path (Join-Path $PSScriptRoot "..")

Push-Location $workspace
try {
    docker compose -f compose.consensus.yml down
}
finally {
    Pop-Location
}
