# -*- coding: utf-8 -*-
"""Redige cg/INVENTAIRE.md a partir des listes etablies par comparaison."""
import collections
import io
import re

import sys
sys.path.insert(0, "D:/cc/traductions/Chaos-Child-FR/cg/outils")
import avancement
_f, _T, faits, reste = avancement.compare()

# Description de chaque sujet, etablie en regardant les images une a une.
D = {
    "config": ("Menu CONFIG complet : intitules des reglages, onglets, bandeau de touches", 3),
    "library": ("Ecran LIBRARY : titre, bandeaux SELECT/CONFIRM/CHANGE PAGE/BACK, NEXT CG/ZOOM, VARIATION", 2),
    "backlog": ("Ecran BACKLOG : logo et bandeau SELECT/PLAY VOICE/BACK", 1),
    "clearlist": ("Liste des fins : bandeau BACK et vignette SILENT SKY END", 1),
    "loadmenu": ("Menu LOAD : logo, NO DATA, DATA BROKEN, bandeau SELECT/CONFIRM/LOCK DATA/BACK", 2),
    "savemenu": ("Menu SAVE : meme structure", 2),
    "qloadmenu": ("Menu QUICK LOAD : meme structure", 2),
    "movmenu": ("Galerie des videos : bandeau SELECT/CONFIRM/BACK et titres sur les bobines", 2),
    "music": ("Lecteur de musique : SELECT/PLAY/STOP/CHANGE PLAY MODE, PLAY ALL/SHUFFLE/REPEAT ALL/REPEAT ONE, NOW PLAYING", 2),
    "menuchip": ("Menu systeme en jeu : BACKLOG, TIPS LIST, CLOSE MENU, QUICK SAVE, CONFIG, EXIT GAME, QUICK LOAD, FULL SCREEN, SAVE, HELP, LOAD, TITLE MENU", 2),
    "gsysmes": ("Fenetre de confirmation : Confirm, deux etats", 1),
    "sysmesswindow": ("Boutons OK / YES / NO, deux etats chacun", 1),
    "help00_steam": ("Aide clavier et souris : une trentaine d'etiquettes", 2),
    "help01": ("Aide manette : tableau FUNCTION / KEY", 2),
    "title_bg": ("Fond du menu titre : la phrase d'accroche sous le logo", 1),
    "mapbg": ("Carte du quartier affichee en jeu : Shibuya Station SURROUNDING AREA MAP", 1),
    "album": ("Planche de vignettes de l'album : reprend les CG, pas de texte propre", 1),
    "FONT_A": ("Atlas de police, rien a traduire", 0),
    "WAVTABLE": ("Table audio, rien a traduire", 0),
    "cc_eff019": ("Commentaires de stream en surimpression : le dernier de la famille 019, les sept autres sont faits", 2),
    "cc_pbg001": ("Bureaux Windows : noms de fichiers et de raccourcis", 1),
    "cc_pbg002": ("Niconiya Live : bandeau du site et titre RETURN OF THE NEW GENERATION MADNESS?", 2),
    "cc_pbg003": ("Niconiya Live, autres plans du meme direct", 2),
    "cc_pbg005": ("Cadres de navigateur des fils @chan : les pages elles-memes sont faites", 1),
    "cc_pbg006": ("Explorateur Windows : Shibuya Photos, colonnes et barre laterale", 1),
    "cc_pbg007": ("Shibuya News : encart de presentation, lecteur, bandeaux publicitaires", 2),
    "cc_pbg008": ("Fil Twipo : profil Club President, tendances, une vingtaine de tweets", 3),
    "cc_pbg014": ("Agregateur nawer : article These Sumo Sticker Memes Will Have You Dying, memes, encarts lateraux", 3),
    "cc_pbg016": ("Wiki Shibuya Serial Deaths Aggregator : sommaire, rubriques, listes de liens", 3),
    "cc_pbg020": ("Messagerie Acq : conversations Ami-chan / Ed Lucas / Max Cady", 2),
    "cc_pbg030": ("Niconiya Douga : titre [Scoop] Tracking the Mystery of Shibuya's Sumo Stickers, commentaires", 2),
    "cc_pbg031": ("Niconiya News : article Today's News with Watabe Tomoaki, commentaires, encarts", 3),
    "cc_pbg032": ("Amaba Blog Sumo Sticker Hunter : en-tete, profil, article", 3),
    "cc_pbg039": ("Interface du jeu en ligne : onglets TALK / BATTLE / EVENT", 1),
    "cc_pbg040": ("Carte de Shibuya annotee : noms de rues, de batiments et de stations", 3),
    "cc_pbg045": ("Site Peoh : navigation, titre de la video, encarts publicitaires", 2),
    "cc_pbg046": ("Site Peoh, autres plans", 2),
    "cc_pbg047": ("PHONEDROID / Speech Waveform Soft : arborescences Library et Effect en entier", 2),
    "cc_pbg050": ("Blog Amaba Sumo Sticker Hunter : article long et ses dix commentaires", 3),
    "cc_ibg001": ("Ecran geant : EMERGENCY BULLETIN / EARTHQUAKE, en perspective et en trame de diodes", 3),
    "cc_ibg007": ("Couverture du magazine LO TYPE", 1),
    "cc_ibg008": ("Couverture du magazine Cal Gal : 100 GIRL FALL ITEMS TO MAKE ANY GUY FALL IN LOVE WITH YOU", 1),
    "cc_ibg010": ("Journal ouvert : colonnes en japonais, verifier s'il reste de l'anglais", 1),
    "cc_ibg047": ("Smartphone, direct [News] Hunting Shibuya's Mysterious Sumo Stickers", 1),
    "cc_ibg048": ("Banderole manuscrite d'un ballon : Please let the bulb be found", 1),
    "cc_ibg055": ("Sachet dried emperor squiddy", 1),
    "cc_ibg081": ("Carte du cafe : MENU, Coffee, Black Tea, Soft Drinks, Lunch Special of the Day", 2),
    "cc_ibg082": ("Page de magazine sur le test de Rorschach : titre et deux paragraphes", 2),
    "cc_ibg087": ("Telephone : CALL HISTORY, INCOMING, OUTGOING, WED OCT 29, 0 CALLS", 1),
    "cc_ibg109": ("Carton de nom YAMAZOE UKI", 1),
    "cc_ibg123": ("Carte d'enquete punaisee : Love Hotel Case, Don't Look, noms de rues", 2),
    "cc_ibg042": ("Enseigne HOTEL Fairy's Dance et ses horaires", 1),
    "cc_ibg050": ("Affiche LET'S BUILD A GUNVARREL PROJECT", 1),
    "cc_ibg079": ("Carte de soins au nom de Senri Minamisawa", 1),
    "cc_ibg092": ("Lettre manuscrite To my beloved family, une page entiere", 3),
    "cc_ibg108": ("Carton de nom AOZAKI YUME", 1),
    "cc_ibg118": ("Facade AI TOKYO GENERAL HOSPITAL", 1),
    "cc_ibg130": ("Tableau d'enquete : carte de Shibuya et une quinzaine de pense-betes manuscrits, six etats", 3),
    "cc_ibg206": ("Salle de classe, affichette au mur", 1),
    "CC_HANA_": ("Repliques de tchat en surimpression sur les CG de Hana", 1),
    "ev_han001": ("CG de Hana : ecran de jeu et dos de livres", 1),
    "ev_han003": ("CG de Hana : dos de livres", 1),
}
DEFAUT = ("Non examine individuellement, meme famille que les precedents", 2)
EFFORT = {0: "-", 1: "leger", 2: "moyen", 3: "lourd"}

BG = {
    "bg0201": "Entree du lycee pendant le festival : Hekiho Festival, Cultural Festival, Hekiho Academy, Entrance, Welcome",
    "bg0202": "Salle de classe : panneaux au mur",
    "bg0203": "Couloir du festival : banderole Hekiho Festival et affiches des clubs",
    "bg0205": "Couloir, affiches",
    "bg0208": "Salle du journal : carte murale, tableau, documents",
    "bg0302": "Entree de l'hotel Fairy's Dance : enseigne au neon, nom propre (garde dans le texte) : rien a traduire",
    "bg0426": "Devanture du fleuriste : SUN BLOOMS, ardoises de prix",
    "bg0501": "Facade AI TOKYO GENERAL HOSPITAL",
    "bg0502": "Hopital, autre plan",
    "bg0504": "Hopital, couloirs et affichettes",
    "bg0509": "Hopital, affichettes",
    "bg0601": "Clinique AOBA CLINIC : plaque et horaires",
    "bg0604": "Accueil de la clinique : RECEPTION et affiches",
}


def racine(n):
    b = n.rsplit(".", 1)[0]
    m = re.match(r"(cc_pbg\d+|cc_ibg\d+|bg\d{4}|CC_HANA_|ev_han\d+|cc_eff\d+)", b)
    return m.group(1) if m else b


g = collections.OrderedDict()
for n in reste:
    g.setdefault(racine(n), []).append(n)

lignes = []
for k, v in g.items():
    if k in BG:
        d, e = BG[k], 1
    else:
        d, e = D.get(k, DEFAUT)
    lignes.append((k, v, d, e))

UI = ["config", "library", "backlog", "clearlist", "loadmenu", "savemenu", "qloadmenu",
      "movmenu", "music", "menuchip", "gsysmes", "sysmesswindow", "help00_steam",
      "help01", "title_bg", "mapbg", "album", "FONT_A", "WAVTABLE"]

out = []
w = out.append
w("# Inventaire des images a traduire")
w("")
w("Etabli le 23 octobre 2026 en comparant, entree par entree, l'archive")
w("`languagebarrier/c0data.mpk` installee dans le jeu a la reference anglaise du")
w("Committee of Zero (`languagebarrier/backup0data.mpk`, mise de cote par")
w("LanguageBarrier avant notre patch). Une entree qui en differe a ete retouchee")
w("par l'equipe ; une entree identique est restee telle quelle.")
w("")
w("`c0data.mpk` est l'archive de **surcharge** du patch anglais : elle ne contient")
w("que des fichiers que le Committee of Zero a eu besoin de refaire, c'est-a-dire")
w("des images **porteuses de texte**. Tout ce qui n'a pas ete retouche est donc")
w("encore en anglais a l'ecran. Verifie par echantillon sur chaque famille.")
w("")
w("| | Entrees |")
w("|---|---|")
w("| Total dans l'archive | **%d** |" % (len(faits) + len(reste)))
w("| Deja traduites | **%d** (%.0f %%) |" % (len(faits), 100.0 * len(faits) / (len(faits) + len(reste))))
w("| Restantes | **%d** (%.0f %%) |" % (len(reste), 100.0 * len(reste) / (len(faits) + len(reste))))
w("")
w("Les %d restantes se ramenent a **%d sujets** : beaucoup de fichiers sont le meme"
  % (len(reste), len(lignes)))
w("decor a plusieurs eclairages (jour, soir, nuit, pluie) ou le meme ecran a")
w("plusieurs etats. Traduire un sujet, c'est reporter le meme calque sur ses")
w("variantes.")
w("")
w("Effort : *leger* = une poignee d'etiquettes ; *moyen* = un ecran entier ;")
w("*lourd* = une page de texte suivi.")
w("")


def table(titre, filtre):
    w("## " + titre)
    w("")
    w("| Sujet | Fichiers | Contenu | Effort |")
    w("|---|---|---|---|")
    for k, v, d, e in lignes:
        if filtre(k):
            w("| `%s` | %d | %s | %s |" % (k, len(v), d, EFFORT[e]))
    w("")


table("Interface et menus", lambda k: k in UI)
table("Pages web, forums et logiciels",
      lambda k: k.startswith("cc_pbg") or k == "cc_eff019")
table("Objets, documents et panneaux (plans rapproches)",
      lambda k: k.startswith("cc_ibg") or k.startswith("CC_HANA") or k.startswith("ev_han"))
table("Decors (une traduction, plusieurs eclairages)", lambda k: k in BG)

w("## Liste complete des fichiers restants")
w("")
w("```")
for k, v, d, e in lignes:
    w("%-14s %s" % (k, " ".join(v)))
w("```")
w("")
w("## Deja traduit")
w("")
w("```")
w(" ".join(faits))
w("```")

io.open(r"D:/cc/traductions/Chaos-Child-FR/cg/INVENTAIRE.md", "w",
        encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print("ecrit, %d lignes" % len(out))
