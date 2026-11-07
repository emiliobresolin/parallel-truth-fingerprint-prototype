[CmdletBinding()]
param([switch]$Smoke, [string]$Resume = '')
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectRoot '.venv-backup\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Ambiente Python ausente.' }
$records = Join-Path $projectRoot 'output\dissertacao\professor_inputs\p23_verificacao'
[void][System.IO.Directory]::CreateDirectory($records)
$lockHandle = $null
$awake = $false
Push-Location $projectRoot
try {
    $lockHandle = [System.IO.File]::Open((Join-Path $records 'execucao.lock'), [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    if (-not ('P23ExecutionState' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class P23ExecutionState {
    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern uint SetThreadExecutionState(uint flags);
}
'@
    }
    $awake = ([P23ExecutionState]::SetThreadExecutionState(2147483649) -ne 0)
    if (-not $awake) { throw 'Nao foi possivel impedir a suspensao automatica.' }
    $evaluationArguments = @('-B','-u',(Join-Path $PSScriptRoot 'run_p23_custom_evaluation.py'))
    if ($Smoke) { $evaluationArguments += '--smoke' }
    if ($Resume) { $evaluationArguments += @('--resume',$Resume) }
    Write-Host 'P23: uma coleta do compressor, cinco seeds e vinte modelos pareados.'
    Write-Host 'Mantenha o computador na energia, Docker Desktop e este terminal abertos.'
    & $python @evaluationArguments
    if ($LASTEXITCODE -ne 0) { throw 'Execucao incompleta; consulte o console.log da sessao.' }
}
finally {
    if ($awake) { [void][P23ExecutionState]::SetThreadExecutionState(2147483648) }
    if ($null -ne $lockHandle) { $lockHandle.Dispose() }
    Pop-Location
}
