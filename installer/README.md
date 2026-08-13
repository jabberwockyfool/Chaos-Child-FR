# Installeur du patch FR

Produit un `.exe` unique qui détecte le jeu, sauvegarde les fichiers d'origine et
copie le contenu de `DIST/` à la racine de CHAOS;CHILD.

## Principe

`DIST/` est l'arborescence **telle qu'elle doit apparaître à la racine du jeu** :

```
DIST/
└── languagebarrier/
    ├── c0data.mpk      (CG, menus, textures FR)
    ├── enscript.mpk    (scripts / dialogues FR)
    └── subs/           (sous-titres OP/ED + polices)
```

Le patch FR se pose **par-dessus** le patch anglais du Committee of Zero (v2.2.0) :
l'installeur refuse d'aller plus loin sans confirmation si `languagebarrier/` est absent.

## Build

```powershell
# tout en un : assemble DIST/ puis compile l'installeur
pwsh -ExecutionPolicy Bypass -File installer\build-installer.ps1

# variantes
... -Version 1.1.0     # surcharge la version affichée
... -SkipDist          # réutilise le DIST/ déjà assemblé
```

Sortie : `installer/output/ChaosChildFR-Setup-<version>.exe`

Prérequis : [Inno Setup 6](https://jrsoftware.org/isdl.php) —
`winget install -e --id JRSoftware.InnoSetup`.
Et `git lfs pull` avant le build (sinon `c0data.mpk` n'est qu'un pointeur LFS ;
`build-dist.ps1` s'arrête avec un message explicite dans ce cas).

## Ce que fait l'installeur

1. **Détection du jeu** — clé de désinstallation Steam (appid `970570`), puis
   `libraryfolders.vdf` pour les bibliothèques secondaires, puis le registre GOG.
   À défaut, le joueur choisit le dossier ; on valide la présence de `Game.exe`.
2. **Sauvegarde** — chaque fichier listé dans `manifest.txt` et déjà présent dans le jeu
   est copié vers `languagebarrier\frpatch\backup\`, **une seule fois** (une réinstallation
   n'écrase pas la sauvegarde d'origine avec des fichiers déjà francisés). Le manifeste est
   déposé là par le code et non via `[Files]` : Inno supprime ses propres fichiers installés
   *avant* l'étape de restauration, le désinstalleur ne le retrouverait plus.
3. **Copie** de `DIST/*` à la racine du jeu.
4. **Désinstallation** — restaure les fichiers anglais depuis la sauvegarde, supprime
   ceux que le patch FR avait ajoutés, puis nettoie `languagebarrier\frpatch\`.

## Ajouter un fichier au patch

Éditer la liste `$Payload` en tête de [build-dist.ps1](build-dist.ps1) : un chemin
relatif à la racine du dépôt, fichier ou dossier (copié récursivement). Le manifeste,
la sauvegarde et la désinstallation suivent automatiquement.
