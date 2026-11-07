[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectRoot '.venv-backup\Scripts\python.exe'
$config = Join-Path $projectRoot 'configs\experiments\p21-public-48epochs-v1.json'
$records = Join-Path $projectRoot 'output\dissertacao\professor_inputs\p21_treino_ampliado\v1'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Ambiente Python .venv-backup ausente.' }
if (-not (Test-Path -LiteralPath $config -PathType Leaf)) { throw 'Configuracao P21 ainda nao finalizada.' }
$runLock = $null
$sleepGuard = $false
Push-Location $projectRoot
try {
    $runLock = [System.IO.File]::Open((Join-Path $records 'execucao.lock'), [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    if (-not ('P21ExecutionState' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class P21ExecutionState {
    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern uint SetThreadExecutionState(uint flags);
}
'@
    }
    $sleepGuard = ([P21ExecutionState]::SetThreadExecutionState(2147483649) -ne 0)
    if (-not $sleepGuard) { Write-Warning 'Nao foi possivel impedir a suspensao automatica; confira energia.' }
    Write-Host 'P21: ADFA-LD, LID-DS 2021 e HAI 23.05; teto LSTM 48 epocas.'
    Write-Host 'Mantenha o computador na energia e este terminal aberto.'
    & $python -B -u (Join-Path $PSScriptRoot 'run_p21_extended_training.py')
    if ($LASTEXITCODE -ne 0) { throw 'Execucao incompleta. Consulte o log exibido; o comando permite retomada.' }
    Write-Host 'Execucao concluida e resumo autenticado. Avise para analisarmos os resultados.'
}
finally {
    if ($sleepGuard) { [void][P21ExecutionState]::SetThreadExecutionState(2147483648) }
    if ($null -ne $runLock) { $runLock.Dispose() }
    Pop-Location
}
