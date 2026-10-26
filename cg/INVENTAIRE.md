# Inventaire des images a traduire

Etabli le 23 octobre 2026 en comparant, entree par entree, l'archive
`languagebarrier/c0data.mpk` installee dans le jeu a la reference anglaise du
Committee of Zero (`languagebarrier/backup0data.mpk`, mise de cote par
LanguageBarrier avant notre patch). Une entree qui en differe a ete retouchee
par l'equipe ; une entree identique est restee telle quelle.

`c0data.mpk` est l'archive de **surcharge** du patch anglais : elle ne contient
que des fichiers que le Committee of Zero a eu besoin de refaire, c'est-a-dire
des images **porteuses de texte**. Tout ce qui n'a pas ete retouche est donc
encore en anglais a l'ecran. Verifie par echantillon sur chaque famille.

| | Entrees |
|---|---|
| Total dans l'archive | **239** |
| Deja traduites | **172** (72 %) |
| Restantes | **67** (28 %) |

Les 67 restantes se ramenent a **43 sujets** : beaucoup de fichiers sont le meme
decor a plusieurs eclairages (jour, soir, nuit, pluie) ou le meme ecran a
plusieurs etats. Traduire un sujet, c'est reporter le meme calque sur ses
variantes.

Effort : *leger* = une poignee d'etiquettes ; *moyen* = un ecran entier ;
*lourd* = une page de texte suivi.

## Interface et menus

| Sujet | Fichiers | Contenu | Effort |
|---|---|---|---|
| `FONT_A` | 1 | Atlas de police, rien a traduire | - |
| `WAVTABLE` | 1 | Table audio, rien a traduire | - |
| `album` | 1 | Planche de vignettes de l'album : reprend les CG, pas de texte propre | leger |

## Pages web, forums et logiciels

| Sujet | Fichiers | Contenu | Effort |
|---|---|---|---|
| `cc_eff019` | 1 | Commentaires de stream en surimpression : le dernier de la famille 019, les sept autres sont faits | moyen |
| `cc_pbg002` | 2 | Niconiya Live : bandeau du site et titre RETURN OF THE NEW GENERATION MADNESS? | moyen |
| `cc_pbg003` | 2 | Niconiya Live, autres plans du meme direct | moyen |
| `cc_pbg006` | 1 | Explorateur Windows : Shibuya Photos, colonnes et barre laterale | leger |
| `cc_pbg007` | 1 | Shibuya News : encart de presentation, lecteur, bandeaux publicitaires | moyen |
| `cc_pbg008` | 2 | Fil Twipo : profil Club President, tendances, une vingtaine de tweets | lourd |
| `cc_pbg014` | 1 | Agregateur nawer : article These Sumo Sticker Memes Will Have You Dying, memes, encarts lateraux | lourd |
| `cc_pbg016` | 1 | Wiki Shibuya Serial Deaths Aggregator : sommaire, rubriques, listes de liens | lourd |
| `cc_pbg020` | 5 | Messagerie Acq : conversations Ami-chan / Ed Lucas / Max Cady | moyen |
| `cc_pbg030` | 3 | Niconiya Douga : titre [Scoop] Tracking the Mystery of Shibuya's Sumo Stickers, commentaires | moyen |
| `cc_pbg031` | 2 | Niconiya News : article Today's News with Watabe Tomoaki, commentaires, encarts | lourd |
| `cc_pbg032` | 3 | Amaba Blog Sumo Sticker Hunter : en-tete, profil, article | lourd |
| `cc_pbg040` | 3 | Carte de Shibuya annotee : noms de rues, de batiments et de stations | lourd |
| `cc_pbg045` | 1 | Site Peoh : navigation, titre de la video, encarts publicitaires | moyen |
| `cc_pbg046` | 2 | Site Peoh, autres plans | moyen |
| `cc_pbg047` | 1 | PHONEDROID / Speech Waveform Soft : arborescences Library et Effect en entier | moyen |
| `cc_pbg050` | 1 | Blog Amaba Sumo Sticker Hunter : article long et ses dix commentaires | lourd |

## Objets, documents et panneaux (plans rapproches)

| Sujet | Fichiers | Contenu | Effort |
|---|---|---|---|
| `cc_ibg001` | 1 | Ecran geant : EMERGENCY BULLETIN / EARTHQUAKE, en perspective et en trame de diodes | lourd |
| `cc_ibg007` | 1 | Couverture du magazine LO TYPE | leger |
| `cc_ibg008` | 1 | Couverture du magazine Cal Gal : 100 GIRL FALL ITEMS TO MAKE ANY GUY FALL IN LOVE WITH YOU | leger |
| `cc_ibg010` | 1 | Journal ouvert : colonnes en japonais, verifier s'il reste de l'anglais | leger |
| `cc_ibg042` | 1 | Enseigne HOTEL Fairy's Dance et ses horaires | leger |
| `cc_ibg047` | 1 | Smartphone, direct [News] Hunting Shibuya's Mysterious Sumo Stickers | leger |
| `cc_ibg048` | 1 | Banderole manuscrite d'un ballon : Please let the bulb be found | leger |
| `cc_ibg050` | 1 | Affiche LET'S BUILD A GUNVARREL PROJECT | leger |
| `cc_ibg055` | 1 | Sachet dried emperor squiddy | leger |
| `cc_ibg079` | 1 | Carte de soins au nom de Senri Minamisawa | leger |
| `cc_ibg081` | 1 | Carte du cafe : MENU, Coffee, Black Tea, Soft Drinks, Lunch Special of the Day | moyen |
| `cc_ibg082` | 1 | Page de magazine sur le test de Rorschach : titre et deux paragraphes | moyen |
| `cc_ibg087` | 1 | Telephone : CALL HISTORY, INCOMING, OUTGOING, WED OCT 29, 0 CALLS | leger |
| `cc_ibg092` | 1 | Lettre manuscrite To my beloved family, une page entiere | lourd |
| `cc_ibg108` | 1 | Carton de nom AOZAKI YUME | leger |
| `cc_ibg109` | 1 | Carton de nom YAMAZOE UKI | leger |
| `cc_ibg118` | 1 | Facade AI TOKYO GENERAL HOSPITAL | leger |
| `cc_ibg123` | 1 | Carte d'enquete punaisee : Love Hotel Case, Don't Look, noms de rues | moyen |
| `cc_ibg130` | 6 | Tableau d'enquete : carte de Shibuya et une quinzaine de pense-betes manuscrits, six etats | lourd |
| `cc_ibg206` | 1 | Salle de classe, affichette au mur | leger |
| `ev_han001` | 5 | CG de Hana : ecran de jeu et dos de livres | leger |
| `ev_han003` | 1 | CG de Hana : dos de livres | leger |

## Decors (une traduction, plusieurs eclairages)

| Sujet | Fichiers | Contenu | Effort |
|---|---|---|---|
| `bg0302` | 1 | Entree de l'hotel Fairy's Dance : enseigne au neon, nom propre (garde dans le texte) : rien a traduire | leger |

## Liste complete des fichiers restants

```
FONT_A         FONT_A.dds
WAVTABLE       WAVTABLE.dat
album          album.dds
bg0302         bg0302aa.png
cc_eff019      cc_eff019h.dds
cc_ibg001      cc_ibg001a.png
cc_ibg007      cc_ibg007a.png
cc_ibg008      cc_ibg008a.png
cc_ibg010      cc_ibg010a.png
cc_ibg042      cc_ibg042a.png
cc_ibg047      cc_ibg047a.png
cc_ibg048      cc_ibg048b.png
cc_ibg050      cc_ibg050a.png
cc_ibg055      cc_ibg055a.png
cc_ibg079      cc_ibg079a.png
cc_ibg081      cc_ibg081a.png
cc_ibg082      cc_ibg082a.png
cc_ibg087      cc_ibg087a.png
cc_ibg092      cc_ibg092a.png
cc_ibg108      cc_ibg108a.png
cc_ibg109      cc_ibg109a.png
cc_ibg118      cc_ibg118a.png
cc_ibg123      cc_ibg123a.png
cc_ibg130      cc_ibg130a.png cc_ibg130b.png cc_ibg130c.png cc_ibg130d.png cc_ibg130e.png cc_ibg130f.png
cc_ibg206      cc_ibg206a.png
cc_pbg002      cc_pbg002a.png cc_pbg002b.png
cc_pbg003      cc_pbg003a.png cc_pbg003b.png
cc_pbg006      cc_pbg006a.png
cc_pbg007      cc_pbg007a.png
cc_pbg008      cc_pbg008aa.png cc_pbg008ab.png
cc_pbg014      cc_pbg014ab.png
cc_pbg016      cc_pbg016a.png
cc_pbg020      cc_pbg020a.png cc_pbg020b.png cc_pbg020c.png cc_pbg020d.png cc_pbg020e.png
cc_pbg030      cc_pbg030a.png cc_pbg030b.png cc_pbg030c.png
cc_pbg031      cc_pbg031a.png cc_pbg031b.png
cc_pbg032      cc_pbg032a.png cc_pbg032b.png cc_pbg032c.png
cc_pbg040      cc_pbg040a.png cc_pbg040b.png cc_pbg040c.png
cc_pbg045      cc_pbg045a.png
cc_pbg046      cc_pbg046a.png cc_pbg046b.png
cc_pbg047      cc_pbg047a.png
cc_pbg050      cc_pbg050ab.png
ev_han001      ev_han001a.png ev_han001b.png ev_han001c.png ev_han001d.png ev_han001e.png
ev_han003      ev_han003a.png
```

## Deja traduit

```
CC_HANA_001.png CC_HANA_002.png CC_HANA_003.png CC_HANA_004.png CC_HANA_005.png CC_HANA_006.png CC_HANA_007.png CC_HANA_008_A.png CC_HANA_008_B.png CC_HANA_009_A.png CC_HANA_009_B.png Z_WARNING.png backlog.dds bg0201aa2.png bg0201na2.png bg0202aa.png bg0202aa2.png bg0202aa3.png bg0202na.png bg0203aa4.png bg0205aa2.png bg0208aa1.png bg0208aa2.png bg0208aa4.png bg0208aa5.png bg0208aa6.png bg0208ac1.png bg0208ac2.png bg0208ea1.png bg0208ea2.png bg0208na.png bg0208na1.png bg0208na3.png bg0209aa.png bg0209ac.png bg0209ea.png bg0209na.png bg0209na1.png bg0426aa.png bg0501aa.png bg0501na.png bg0501na1.png bg0501na2.png bg0502aa.png bg0502na.png bg0504na.png bg0504na1.png bg0504na2.png bg0509na.png bg0509na1.png bg0601aa.png bg0601ar.png bg0601ea.png bg0601na.png bg0604aa.png bg0604ea.png bg0604na.png cc_eff019a.png cc_eff019b.png cc_eff019c.png cc_eff019d.dds cc_eff019e.dds cc_eff019f.dds cc_eff019g.dds cc_ibg054a.png cc_ibg058a_a.png cc_ibg058a_b.png cc_ibg058a_c.png cc_ibg058a_d.png cc_ibg058a_e.png cc_ibg060a.png cc_ibg098a.png cc_ibg100a.png cc_ibg139a.png cc_ibg139b.png cc_ibg206b.png cc_ibgupmovie_001_a.png cc_ibgupmovie_001_b.png cc_ibgupmovie_001_c.png cc_ibgupmovie_001_d.png cc_ibgupmovie_001_e.png cc_ibgupmovie_001_f.png cc_ibgupmovie_002_a.png cc_ibgupmovie_002_b.png cc_ibgupmovie_003_a.png cc_ibgupmovie_003_b.png cc_ibgupmovie_003_c.png cc_ibgupmovie_003_d.png cc_ibgupmovie_003_e.png cc_ibgupmovie_004_a.png cc_ibgupmovie_004_b.png cc_ibgupmovie_005_a.png cc_ibgupmovie_005_b.png cc_ibgupmovie_005_c.png cc_ibgupmovie_005_d.png cc_ibgupmovie_006_a.png cc_ibgupmovie_007_a.png cc_ibgupmovie_008_a.png cc_ibgupmovie_009_a.png cc_ibgupmovie_009_b.png cc_ibgupmovie_009_c.png cc_ibgupmovie_009_d.png cc_ibgupmovie_009_e.png cc_ibgupmovie_009_f.png cc_ibgupmovie_010_a.png cc_ibgupmovie_011_a.png cc_ibgupmovie_011_b.png cc_ibgupmovie_011_c.png cc_ibgupmovie_011_d.png cc_ibgupmovie_012_a.png cc_ibgupmovie_013_a.png cc_ibgupmovie_013_b.png cc_ibgupmovie_013_c.png cc_ibgupmovie_013_d.png cc_ibgupmovie_013_e.png cc_pbg001a.png cc_pbg001b.png cc_pbg001c.png cc_pbg001d.png cc_pbg001e.png cc_pbg005aa.png cc_pbg005ab.png cc_pbg005ba.png cc_pbg005bb.png cc_pbg005ca.png cc_pbg005cb.png cc_pbg005da.png cc_pbg005db.png cc_pbg005ea.png cc_pbg005eb.png cc_pbg005fa.png cc_pbg005fb.png cc_pbg014aa.png cc_pbg029a.png cc_pbg037a.png cc_pbg037aa.png cc_pbg037ab.png cc_pbg038a.png cc_pbg039a.png cc_pbg039b.png cc_pbg039c.png cc_pbg039d.png cc_pbg042a.png cc_pbg043a.png cc_pbg043b.png cc_pbg048a.png cc_pbg049a.png cc_pbg050aa.png clearlist.dds config.dds data01.dds ev_zzz007a.png ev_zzz007b.png ev_zzz012d.png gsysmes.dds help00_steam.dds help01.dds library.dds loadmenu.dds mapbg.dds mapparts.dds menuchip.dds movmenu.dds music.dds nameplate.dds qloadmenu.dds savemenu.dds sysmesswindow.dds tipschips.dds title_bg.dds title_chip.dds tutorial.png
```
