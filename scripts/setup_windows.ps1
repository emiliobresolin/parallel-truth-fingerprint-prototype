<#
Creates or repairs the project-local Windows environment from uv.lock.
The script can be invoked from any working directory.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$uvVersion = '0.12.13'

$candidates = @()
$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) { $candidates += @{ Executable = $py.Source; Arguments = @('-3.14') } }
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCommand) { $candidates += @{ Executable = $pythonCommand.Source; Arguments = @() } }

$python = $null
$pythonArgs = @()
foreach ($candidate in $candidates) {
    & $candidate.Executable @($candidate.Arguments) -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 14) else 1)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $python = $candidate.Executable
        $pythonArgs = $candidate.Arguments
        break
    }
}
if (-not $python) { throw 'Python 3.14 or newer is required but was not found.' }

Push-Location $projectRoot
try {
    $bootstrapRoot = Join-Path $projectRoot '.tmp\uv-bootstrap'
    $bootstrapPython = Join-Path $bootstrapRoot 'Scripts\python.exe'
    $bootstrapUv = Join-Path $bootstrapRoot 'Scripts\uv.exe'
    if (-not (Test-Path -LiteralPath $bootstrapPython -PathType Leaf)) {
        & $python @pythonArgs -m venv $bootstrapRoot
        if ($LASTEXITCODE -ne 0) { throw 'Unable to create the local uv bootstrap environment.' }
    }
    & $bootstrapPython -m pip install --disable-pip-version-check "uv==$uvVersion"
    if ($LASTEXITCODE -ne 0) { throw "Unable to install uv $uvVersion in the local bootstrap environment." }

    & $bootstrapUv sync --all-extras --locked --link-mode copy --reinstall-package kaggle
    if ($LASTEXITCODE -ne 0) { throw 'Unable to synchronize the project environment from uv.lock.' }
}
finally {
    Pop-Location
}

Write-Host "Project environment ready at $(Join-Path $projectRoot '.venv')"
