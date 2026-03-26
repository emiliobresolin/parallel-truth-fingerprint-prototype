param(
    [string]$OutputRoot = ".cometbft/testnet"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$workspace = Resolve-Path (Join-Path $PSScriptRoot "..")
$outputPath = Join-Path $workspace $OutputRoot
$stateRoot = Join-Path $workspace ".cometbft/state"
$cometRoot = Split-Path $outputPath -Parent
$stagingName = "testnet-staging-" + [guid]::NewGuid().ToString("N")
$stagingRoot = Join-Path $cometRoot $stagingName

function Remove-DirectoryIfPresent {
    param([string]$Path)

    if (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
}

function Assert-GeneratedTestnet {
    param([string]$RootPath)

    foreach ($nodeName in @("node0", "node1", "node2")) {
        $configPath = Join-Path $RootPath "$nodeName/config/config.toml"
        $genesisPath = Join-Path $RootPath "$nodeName/config/genesis.json"
        $validatorKeyPath = Join-Path $RootPath "$nodeName/config/priv_validator_key.json"

        if (-not (Test-Path -LiteralPath $configPath)) {
            throw "CometBFT testnet generation failed: missing $configPath"
        }
        if (-not (Test-Path -LiteralPath $genesisPath)) {
            throw "CometBFT testnet generation failed: missing $genesisPath"
        }
        if (-not (Test-Path -LiteralPath $validatorKeyPath)) {
            throw "CometBFT testnet generation failed: missing $validatorKeyPath"
        }
    }
}

Remove-DirectoryIfPresent $stagingRoot
New-Item -ItemType Directory -Force -Path $cometRoot | Out-Null

try {
    docker run --rm `
      -v "${workspace}:/workspace" `
      -w /workspace `
      cometbft/cometbft:latest `
      testnet --v 3 --o "/workspace/.cometbft/$stagingName"

    Assert-GeneratedTestnet -RootPath $stagingRoot

    Remove-DirectoryIfPresent $outputPath
    Remove-DirectoryIfPresent $stateRoot

    Move-Item -LiteralPath $stagingRoot -Destination $outputPath
    New-Item -ItemType Directory -Force -Path $stateRoot | Out-Null

    @(
        @{ Name = "node0"; Proxy = "tcp://abci-node0:26658" }
        @{ Name = "node1"; Proxy = "tcp://abci-node1:26658" }
        @{ Name = "node2"; Proxy = "tcp://abci-node2:26658" }
    ) | ForEach-Object {
        $configPath = Join-Path $outputPath "$($_.Name)/config/config.toml"
        $content = Get-Content -LiteralPath $configPath -Raw
        $content = $content -replace 'proxy_app = "tcp://127.0.0.1:26658"', "proxy_app = `"$($_.Proxy)`""
        $content = $content -replace 'laddr = "tcp://127.0.0.1:26657"', 'laddr = "tcp://0.0.0.0:26657"'
        Set-Content -LiteralPath $configPath -Value $content

        $nodeState = Join-Path $stateRoot $_.Name
        New-Item -ItemType Directory -Force -Path $nodeState | Out-Null
    }
}
catch {
    Remove-DirectoryIfPresent $stagingRoot
    throw
}

Write-Host "Initialized CometBFT testnet under $outputPath"
Write-Host "ABCI state directories initialized under $stateRoot"
