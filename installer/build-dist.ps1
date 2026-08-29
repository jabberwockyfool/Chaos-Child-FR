<#
    build-dist.ps1
    Assemble le dossier DIST/ : l'arborescence exacte a poser a la racine du jeu
    (par-dessus le patch Committee of Zero), puis genere le manifeste utilise par
    l'installeur pour la sauvegarde et la desinstallation.

    Usage :  pwsh -ExecutionPolicy Bypass -File installer\build-dist.ps1
#>
[CmdletBinding()]
param(
    [string]$Root,
    [string]$Dist,
    [string]$Manifest
)

$ErrorActionPreference = 'Stop'

if (-not $Root)     { $Root     = Split-Path -Parent $PSScriptRoot }
if (-not $Dist)     { $Dist     = Join-Path $Root 'DIST' }
if (-not $Manifest) { $Manifest = Join-Path $PSScriptRoot 'manifest.txt' }

# Chemins relatifs (depuis la racine du depot) a embarquer dans DIST.
# Un dossier est copie recursivement, un fichier tel quel.
$Payload = @(
    'languagebarrier\c0data.mpk',
    'languagebarrier\enscript.mpk',
    'languagebarrier\subs',
    # Rich Presence Discord : l'exe, plus le boot.bat qui le lance avec le jeu.
    # Le boot.bat d'origine est sauvegarde puis restaure par l'installeur, comme
    # tout fichier du manifeste.
    'languagebarrier\rpc\ChaosChildRPC.exe',
    'boot.bat'
)

function Assert-NotLfsPointer([string]$Path) {
    $fi = Get-Item -LiteralPath $Path
    if ($fi.Length -lt 1024) {
        $head = Get-Content -LiteralPath $Path -TotalCount 1 -ErrorAction SilentlyContinue
        if ($head -like 'version https://git-lfs*') {
            throw "$($fi.Name) est un pointeur Git LFS et non le vrai fichier. Lance 'git lfs pull' avant de builder."
        }
    }
}

Write-Host "Racine du depot : $Root"
Write-Host "Sortie DIST     : $Dist"

if (Test-Path -LiteralPath $Dist) {
    Write-Host "Nettoyage de DIST/..."
    Remove-Item -LiteralPath $Dist -Recurse -Force
}
New-Item -ItemType Directory -Path $Dist -Force | Out-Null

foreach ($rel in $Payload) {
    $src = Join-Path $Root $rel
    if (-not (Test-Path -LiteralPath $src)) {
        throw "Element de charge utile introuvable : $rel"
    }
    $dst = Join-Path $Dist $rel
    $dstParent = Split-Path -Parent $dst
    New-Item -ItemType Directory -Path $dstParent -Force | Out-Null

    if (Test-Path -LiteralPath $src -PathType Container) {
        Copy-Item -LiteralPath $src -Destination $dst -Recurse -Force
        Get-ChildItem -LiteralPath $dst -Recurse -File | ForEach-Object { Assert-NotLfsPointer $_.FullName }
        $n = (Get-ChildItem -LiteralPath $dst -Recurse -File).Count
        Write-Host ("  + {0,-40} ({1} fichiers)" -f $rel, $n)
    }
    else {
        Assert-NotLfsPointer $src
        Copy-Item -LiteralPath $src -Destination $dst -Force
        $mb = [math]::Round((Get-Item -LiteralPath $dst).Length / 1MB, 1)
        Write-Host ("  + {0,-40} ({1} Mo)" -f $rel, $mb)
    }
}

# Manifeste : un chemin relatif par ligne, tel qu'il apparaitra a la racine du jeu.
$prefix = (Resolve-Path -LiteralPath $Dist).Path.TrimEnd('\') + '\'
$files = Get-ChildItem -LiteralPath $Dist -Recurse -File |
         ForEach-Object { $_.FullName.Substring($prefix.Length) } |
         Sort-Object
# UTF-8 sans BOM : Inno lit ce fichier ligne par ligne, un BOM corromprait le premier chemin.
[System.IO.File]::WriteAllLines($Manifest, [string[]]$files, (New-Object System.Text.UTF8Encoding($false)))

$totalMb = [math]::Round((Get-ChildItem -LiteralPath $Dist -Recurse -File |
            Measure-Object Length -Sum).Sum / 1MB, 1)
Write-Host ""
Write-Host "DIST pret : $($files.Count) fichiers, $totalMb Mo"
Write-Host "Manifeste : $Manifest"
