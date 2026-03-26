param()

$ErrorActionPreference = "Stop"
$workspace = Resolve-Path (Join-Path $PSScriptRoot "..")

Push-Location $workspace
try {
    if (-not (Test-Path ".cometbft/testnet/node0/config/config.toml")) {
        & (Join-Path $PSScriptRoot "init_cometbft_testnet.ps1")
    }

    docker compose -f compose.consensus.yml up -d --build
    Write-Host "Consensus stack started. Node0 RPC: http://127.0.0.1:26657"
}
finally {
    Pop-Location
}
