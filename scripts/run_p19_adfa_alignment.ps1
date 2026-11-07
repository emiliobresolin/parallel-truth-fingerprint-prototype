[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectRoot '.venv-backup\Scripts\python.exe'
$config = Join-Path $projectRoot 'configs\experiments\p19-adfa-aligned-v3.json'
$recordDirectory = Join-Path $projectRoot 'output\dissertacao\professor_inputs\p19_alinhamento'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Ambiente Python .venv-backup ausente.' }
if (-not (Test-Path -LiteralPath $config -PathType Leaf)) { throw 'Configuracao P19 ainda nao finalizada; consultar a verificacao.' }
$runLock = $null
$sleepGuard = $false
Push-Location $projectRoot
try {
    $runLock = [System.IO.File]::Open((Join-Path $recordDirectory 'execucao.lock'), [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    if (-not ('P19ExecutionState' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class P19ExecutionState {
    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern uint SetThreadExecutionState(uint flags);
}
'@
    }
    $sleepGuard = ([P19ExecutionState]::SetThreadExecutionState(2147483649) -ne 0)
    if (-not $sleepGuard) { Write-Warning 'Nao foi possivel impedir a suspensao automatica; confira a configuracao de energia.' }
    Write-Host 'P19: ADFA-LD, janela 128, avanco 128, agregacao max.'
    Write-Host 'Execucao exploratoria: quatro metodos; cinco seeds da LSTM; oito ajustes no total.'
    Write-Host 'O caminho do log e o progresso serao exibidos abaixo.'
    Write-Host 'Mantenha o computador ligado a energia e este terminal aberto.'
    & $python -B -u (Join-Path $PSScriptRoot 'run_p19_adfa_alignment.py')
    $runExitCode = $LASTEXITCODE
    if ($runExitCode -ne 0) { throw "A execucao terminou com codigo $runExitCode. Consulte o log exibido; o mesmo comando retoma as celulas concluidas." }
    Write-Host 'P19 concluido. Avise para analisarmos os resultados.'
}
finally {
    if ($sleepGuard) { [void][P19ExecutionState]::SetThreadExecutionState(2147483648) }
    if ($null -ne $runLock) { $runLock.Dispose() }
    Pop-Location
}
