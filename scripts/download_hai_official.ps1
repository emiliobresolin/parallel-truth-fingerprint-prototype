<#
Downloads the HAI dataset from the dataset owner's public Kaggle publication.
Kaggle requires a user API token; this script never stores or prints it.
#>
[CmdletBinding()]
param(
    [string]$Destination = "datasets\HAI-23.05-kaggle"
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$kaggle = Join-Path $projectRoot '.venv\Scripts\kaggle.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Project environment not found at $python. Run '.\scripts\setup_windows.ps1' from the repository root."
}
if (-not (Test-Path -LiteralPath $kaggle -PathType Leaf)) {
    throw @'
Kaggle CLI is not installed or authenticated. Create a free Kaggle account,
open https://www.kaggle.com/settings/account, select "Create New Token", and
save the downloaded kaggle.json in %USERPROFILE%\.kaggle\kaggle.json. Then run:
  .\scripts\setup_windows.ps1
and run this script again. Do not commit kaggle.json.
'@
}

if (-not [System.IO.Path]::IsPathRooted($Destination)) {
    $Destination = Join-Path $projectRoot $Destination
}
$Destination = [System.IO.Path]::GetFullPath($Destination)
$projectPrefix = $projectRoot.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
if (-not $Destination.StartsWith($projectPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Destination escapes the repository root: $Destination"
}
New-Item -ItemType Directory -Force -Path $Destination | Out-Null
& $kaggle datasets download --dataset icsdataset/hai-security-dataset --unzip --path $Destination
if ($LASTEXITCODE -ne 0) { throw 'Kaggle could not download the owner-published HAI dataset.' }
Write-Host "Downloaded HAI owner publication to $Destination. Run scripts\qualify_live_run.py next."
