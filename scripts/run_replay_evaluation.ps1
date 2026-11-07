[CmdletBinding()]
param([switch]$Smoke, [switch]$PairedProfiles, [double]$TimeoutHours = 4)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = $null
foreach ($relative in @('.venv\Scripts\python.exe', '.venv-backup\Scripts\python.exe')) {
    $candidate = Join-Path $projectRoot $relative
    if (Test-Path -LiteralPath $candidate -PathType Leaf) { $python = $candidate; break }
}
if (-not $python) { throw 'Python environment missing. Run scripts/setup_windows.ps1 first.' }
$evaluationArguments = @('--timeout-hours', $TimeoutHours)
if ($Smoke) { $evaluationArguments += '--smoke' }
if ($PairedProfiles) { $evaluationArguments += '--paired-profiles' }
& $python -B -u (Join-Path $PSScriptRoot 'run_replay_evaluation.py') @evaluationArguments
if ($LASTEXITCODE -ne 0) { throw 'Evaluation did not complete cleanly. Consult launcher.json and console.log.' }
