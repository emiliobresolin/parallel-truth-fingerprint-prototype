<#
Runs the genuine demo process on Docker's Linux/WSL2 kernel and records its
syscalls. This script deliberately invokes the fail-closed data preflight
first; it does not produce a capture while official HAI or LID bytes are
missing.
#>
[CmdletBinding()]
param(
    [string]$Bucket = "ptfp-syscall-live",
    [int]$Cycles = 30,
    [int]$IntervalSeconds = 5,
    [string]$Scenario = "normal",
    [string]$FaultMode = "none",
    [double]$PowerPct = 65.0,
    [string]$RunId = (Get-Date -Format 'yyyyMMdd-HHmmss')
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Project environment not found at $python. Run '.\scripts\setup_windows.ps1' from the repository root."
}
Push-Location $projectRoot
try {
    & $python scripts\qualify_live_run.py
    if ($LASTEXITCODE -ne 0) {
        throw 'Live evidence preflight failed. Resolve its reported blockers before capturing syscalls.'
    }

    if ($RunId -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') {
        throw 'RunId may contain only letters, numbers, dots, underscores, and hyphens.'
    }
    # An explicit fault is itself the runtime scenario.  Do not let the
    # default "normal" scenario silently override it in scenario_control.
    if ($FaultMode -ne 'none') {
        $Scenario = $FaultMode
    }
    $captureDirectory = Join-Path $projectRoot (Join-Path 'logs\syscall-captures' $RunId)
    if (Test-Path -LiteralPath $captureDirectory) {
        throw "Capture directory already exists: $captureDirectory"
    }
    New-Item -ItemType Directory -Path $captureDirectory | Out-Null
    docker build --tag ptfp-live-edge-capture --file Dockerfile.live-edge-capture .
    if ($LASTEXITCODE -ne 0) { throw 'Unable to build the Linux edge-capture image.' }

    docker run --rm `
        --name ptfp-live-edge-capture `
        --add-host host.docker.internal:host-gateway `
        --mount "type=bind,source=$captureDirectory,target=/captures" `
        --env MQTT_TRANSPORT=real `
        --env MQTT_BROKER_HOST=host.docker.internal `
        --env COMETBFT_RPC_URL=http://host.docker.internal:26657 `
        --env MINIO_ENDPOINT=host.docker.internal:9000 `
        --env MINIO_ACCESS_KEY=minioadmin `
        --env MINIO_SECRET_KEY=minioadmin `
        --env MINIO_BUCKET=$Bucket `
        --env MINIO_SECURE=false `
        --env DEMO_DISABLE_RUNTIME_AUTOENCODER=false `
        --env DEMO_CAMPAIGN_ID=$RunId `
        --env DEMO_SCENARIO=$Scenario `
        --env DEMO_FAULT_MODE=$FaultMode `
        --env DEMO_POWER=$PowerPct `
        --env DEMO_MAX_CYCLES=$Cycles `
        --env DEMO_CYCLE_INTERVAL_SECONDS=$IntervalSeconds `
        --env DEMO_LOG_PATH=/captures/runtime.json `
        ptfp-live-edge-capture
    if ($LASTEXITCODE -ne 0) { throw 'The Linux edge capture failed.' }

    Write-Host "Raw syscall traces and runtime log: $captureDirectory"
}
finally {
    Pop-Location
}
