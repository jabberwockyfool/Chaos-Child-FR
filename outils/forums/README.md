# Pages de forum @chan

Les fils @chan du jeu sont des **images entières** de `c0data.mpk` : un cadre de
navigateur en 1920×1080 (`cc_pbg005Xa.png`) et une page défilante de 1292 de large,
jusqu'à 6000 de haut (`cc_pbg005Xb.png`, `cc_pbg037ab.png`).

## Méthode

On ne recrée pas la page : `page.py` la découpe en bandes d'encre, les classe (en-tête
au pseudo vert, titre rouge, lien bleu, vignette, corps), puis `ecrire.py` efface chaque
ligne de corps et redessine le français **au même endroit** — même x de départ, même
ligne de base. Le cadre, les vignettes, les en-têtes et les boutons ne sont jamais
touchés.

Convention reprise des deux pages déjà traduites par l'équipe : on traduit **le titre et
le corps des messages**, pas les en-têtes (`Name :`, `Submitted :`,
`Anonymous@Reproduction Prohibited`) ni les dates.

Police : Segoe UI Bold 18, encre noire sur fond `#EEEEEE` ; titre 20 en rouge. Les
kaomoji et les caractères absents de Segoe UI (`★`, `゚Д゚`…) sont dessinés avec MS Gothic
via un segment `(texte, couleur, CJK)`.

## Fichiers de fil

Un `fil_*.py` par page : `TITRE` (ou `TITRE_BLOC` quand le titre tient sur deux lignes à
côté des boutons), `CORPS` (une entrée par ligne de corps, dans l'ordre), et `SAUTER`
pour les zones à ne pas toucher (art ASCII).

Une entrée de `CORPS` peut être :
- une chaîne ;
- une liste de segments `[(texte, couleur[, police])]` ;
- un tuple de deux lignes, quand deux lignes se touchent et forment une seule bande.

Si le compte ne tombe pas juste, `ecrire.py` s'arrête en disant combien de lignes il a
trouvées dans l'image : c'est presque toujours une ligne oubliée ou une bande fusionnée.

## Mise en archive

- `remplace.py` réécrit une entrée **sur place** quand le nouveau fichier tient dans le
  créneau de l'ancien (le MPK stocke sans compression, aligné sur 2048) ;
- `reconstruit.py` réécrit l'archive entière en recalculant les offsets, pour les cas où
  le fichier a grossi. Les entrées non remplacées sont recopiées à l'octet près.

Attention : `cg/c0data` n'est pas un miroir exact de l'archive (fichiers de travail, .psd)
— toujours partir de l'archive comme gabarit, jamais du dossier.

## Avancement

Traduits : `cc_pbg005ab`, `cc_pbg005bb` (par l'équipe), puis `cc_pbg005cb`, `cc_pbg005db`,
`cc_pbg005eb`, `cc_pbg005fb`, `cc_pbg037ab` et `cc_pbg037a`.

`cc_pbg037a` est le même fil que `037ab`, mais posé dans la fenêtre du navigateur
(1920×2178). Le forum y est rendu à la **même taille**, simplement décalé de (+30, +58) :
`fil_037a.py` réimporte donc `CORPS` de `fil_037ab.py` et ne redéfinit que les bornes
(`ZONE`, `BORD`) et le bloc de titre.

Restent en anglais, mais ce ne sont pas des forums : `cc_pbg008ab` (fil type Twitter),
`cc_pbg014ab` (agrégateur d'articles) et `cc_pbg050ab` (blog). Ce sont des mises en page
web à plusieurs colonnes, avec du texte sur des fonds variés et mêlé aux images : la
découpe en bandes ne s'y applique pas, il faut y placer chaque bloc à la main.
