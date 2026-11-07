[CmdletBinding()]
param([switch]$Smoke, [switch]$FourEdges, [switch]$ContextualInputs, [switch]$CommonCalibration, [switch]$HartTotalizer, [switch]$GenericPlant)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$taskPython = $null
foreach ($relative in @('.venv\Scripts\python.exe', '.venv-backup\Scripts\python.exe')) {
    $candidate = Join-Path $projectRoot $relative
    if (Test-Path -LiteralPath $candidate -PathType Leaf) { $taskPython = $candidate; break }
}
if (-not $taskPython) { throw 'Python environment missing.' }
$taskArguments = @()
if ($Smoke) { $taskArguments += '--smoke' }
if ($FourEdges) { $taskArguments += '--four-edges' }
if ($ContextualInputs) { $taskArguments += '--contextual-inputs' }
if ($CommonCalibration) { $taskArguments += '--common-calibration' }
if ($HartTotalizer) { $taskArguments += '--hart-totalizer' }
if ($GenericPlant) { $taskArguments += '--generic-plant' }
& $taskPython -B -u (Join-Path $PSScriptRoot 'run_replay_confirmation.py') @taskArguments
if ($LASTEXITCODE -ne 0) { throw 'Confirmation incomplete. Consult summary.json and logs in the printed directory.' }
