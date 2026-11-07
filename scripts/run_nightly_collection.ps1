[CmdletBinding()]
param(
    [double]$Hours = 10,
    [string]$StopAt = '',
    [int]$MaxCampaigns = 0,
    [int]$Cycles = 5,
    [string]$ScenarioCycle = 'normal,normal,normal,normal,normal,normal,normal,normal,normal,single_edge_exclusion'
)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = $null
foreach ($relative in @('.venv\Scripts\python.exe', '.venv-backup\Scripts\python.exe')) {
    $candidate = Join-Path $projectRoot $relative
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        $python = $candidate
        break
    }
}
if (-not $python) { throw 'Python environment missing. Run scripts/setup_windows.ps1 first.' }
$collectionArguments = @('--hours', $Hours, '--max-campaigns', $MaxCampaigns, '--cycles', $Cycles, '--scenario-cycle', $ScenarioCycle)
if ($StopAt) { $collectionArguments += @('--stop-at', $StopAt) }
& $python -B -u (Join-Path $PSScriptRoot 'run_nightly_collection.py') @collectionArguments
if ($LASTEXITCODE -ne 0) { throw 'Collection stopped with an error. Consult the printed summary path.' }
