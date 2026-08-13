<#
    build-installer.ps1
    1. Assemble DIST/ (build-dist.ps1)
    2. Compile installer\ChaosChildFR.iss avec Inno Setup (ISCC.exe)
    -> installer\output\ChaosChildFR-Setup-<version>.exe

    Usage :  pwsh -ExecutionPolicy Bypass -File installer\build-installer.ps1
             ... -Version 1.1.0     (surcharge la version du .iss)
             ... -SkipDist          (reutilise le DIST existant)
#>
[CmdletBinding()]
param(
    [string]$Version,
    [switch]$SkipDist,
    [string]$Iscc
)

$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot

function Find-Iscc {
    if ($Iscc) { return $Iscc }
    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    foreach ($p in @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 5\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe")) {
        if (Test-Path -LiteralPath $p) { return $p }
    }
    return $null
}

if (-not $SkipDist) {
    Write-Host "== Assemblage de DIST/ ==" -ForegroundColor Cyan
    & (Join-Path $here 'build-dist.ps1')
    if ($LASTEXITCODE) { throw "build-dist.ps1 a echoue" }
}

$compiler = Find-Iscc
if (-not $compiler) {
    Write-Host ""
    Write-Warning "Inno Setup (ISCC.exe) est introuvable. Installe-le puis relance :"
    Write-Host "    winget install -e --id JRSoftware.InnoSetup" -ForegroundColor Yellow
    Write-Host "  (ou https://jrsoftware.org/isdl.php)"
    exit 1
}

Write-Host ""
Write-Host "== Compilation de l'installeur ==" -ForegroundColor Cyan
Write-Host "ISCC : $compiler"

$argsList = @()
if ($Version) { $argsList += "/DAppVersion=$Version" }
$argsList += (Join-Path $here 'ChaosChildFR.iss')

& $compiler @argsList
if ($LASTEXITCODE) { throw "ISCC a echoue (code $LASTEXITCODE)" }

$out = Get-ChildItem (Join-Path $here 'output') -Filter '*.exe' -ErrorAction SilentlyContinue |
       Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($out) {
    Write-Host ""
    Write-Host ("Installeur pret : {0} ({1} Mo)" -f $out.FullName, [math]::Round($out.Length / 1MB, 1)) -ForegroundColor Green
}
