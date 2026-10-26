# -*- coding: utf-8 -*-
"""Etiquettes des cinq bureaux Windows (cc_pbg001a..e).

Meme principe que `bureau.py` pour les fils @chan : on reconnait l'anglais au
gabarit (Segoe UI 12), on efface en diffusant le pourtour, on redessine le
francais au meme endroit.

Les noms de marque parodies restent tels quels : Internet Escape, HACHIBASE,
iTumes, RINE, AfterAction, PhotoStore ELEMENT, FireEarth, Macrosoft Axcel,
Winbows Live, EMPIRE SWORD ONLINE.

    python cg/outils/bureaux.py [cc_pbg001a] [--install]
"""
import io
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

RACINE = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.dirname(os.path.dirname(RACINE))
sys.path.insert(0, RACINE)
import localise     # noqa: E402
import mpk          # noqa: E402
import rebouche     # noqa: E402
import remplace     # noqa: E402

JEU = "D:/SteamLibrary/steamapps/common/CHAOS;CHILD/languagebarrier/"
REFERENCE = JEU + "backup0data.mpk"
SORTIE = os.path.join(DEPOT, "cg", "c0data")
SEGOE = "C:/Windows/Fonts/segoeui.ttf"
CORPS = 12

# Par image : (y approximatif de la ligne, x du centre de l'etiquette,
#              anglais, francais). La fenetre de recherche est deduite ;
#              elle n'a qu'a isoler la bonne etiquette.
TABLES = {
    "cc_pbg001a.png": [
        (93, 83, "Computer", "Ordinateur"),
        (91, 211, "Graphics", "Graphiques"),
        (108, 211, "- Shortcut", "- Raccourci"),
        (190, 81, "Recycle Bin", "Corbeille"),
        (189, 209, "Movies", "Vidéos"),
        (205, 209, "- Shortcut", "- Raccourci"),
        (297, 212, "Recovered Files", "Fichiers récupérés"),
        (313, 212, "- Shortcut", "- Raccourci"),
        # la fenetre est bornee a gauche : sinon elle mord sur HACHIBASE
        (405, 212, "Shibuya incident inves...", "Enquête incident Shib...", (135, 320)),
        (421, 212, "- Shortcut", "- Raccourci"),
    ],
    "cc_pbg001b.png": [
        (93, 83, "Computer", "Ordinateur"),
        (190, 81, "Recycle Bin", "Corbeille"),
        (709, 88, "Shared", "Partagé"),
        (729, 83, "- Shortcut", "- Raccourci"),
        (820, 84, "Images", "Images"),
        (836, 84, "- Shortcut", "- Raccourci"),
        (821, 214, "New Genera...", "New Genera..."),
        (838, 218, "- Shortcut", "- Raccourci"),
    ],
    "cc_pbg001c.png": [
        (93, 83, "Computer", "Ordinateur"),
        (191, 81, "Recycle Bin", "Corbeille"),
        (191, 187, "Victim", "Victimes"),
        (206, 189, "-LIST", "-LISTE"),
        (289, 189, "Backup", "Sauvegarde"),
        (399, 187, "confidential", "confidentiel"),
        (627, 82, "New Gen Shortcuts", "Raccourcis New Gen"),
        (737, 81, "2013 Shortcuts", "Raccourcis 2013"),
        (850, 81, "2014 Shortcuts", "Raccourcis 2014"),
        (960, 81, "2015 Shortcuts", "Raccourcis 2015"),
    ],
    "cc_pbg001d.png": [
        (93, 83, "Computer", "Ordinateur"),
        (191, 81, "Trash", "Corbeille"),
        (191, 320, "Drawing", "Dessin"),
        (296, 86, "Internet", "Internet"),
        (406, 80, "Iwa - Shortcut", "Iwa - Raccourci"),
        (513, 78, "Kitties", "Chatons"),
        (529, 84, "- Shortcut", "- Raccourci"),
        (510, 188, "Wallpapers", "Fonds d’écran"),
        (521, 359, "Letters", "Lettres"),
        (627, 78, "Doggos", "Toutous"),
        (643, 81, "- Shortcut", "- Raccourci"),
        (624, 189, "Backup", "Sauvegarde"),
        (631, 354, "Iwa wallpaper", "Fond Iwa"),
        (647, 354, "(Iwallpaper?)", "(Iwallpaper ?)"),
        (737, 79, "Wombats", "Wombats"),
        (753, 79, "- Shortcut", "- Raccourci"),
    ],
    "cc_pbg001e.png": [
        (93, 83, "Computer", "Ordinateur"),
        (191, 81, "Recycle Bin", "Corbeille"),
        (935, 1742, "Charts", "Tableaux"),
        (952, 1742, "- Shortcut", "- Raccourci"),
    ],
}


def dessine(img, modele, y, x, couleur, ombre):
    h, w = modele.shape
    m = modele.astype(float)
    flou = np.asarray(Image.fromarray((m * 255).astype("uint8"))
                      .filter(ImageFilter.MaxFilter(3))
                      .filter(ImageFilter.GaussianBlur(0.9)), dtype=float) / 255.0
    bloc = img[y:y + h, x:x + w]
    t = np.clip(flou * 0.85, 0, 1)[..., None]
    bloc[:] = bloc * (1 - t) + np.array(ombre, dtype=float) * t
    t = m[..., None]
    bloc[:] = bloc * (1 - t) + np.array(couleur, dtype=float) * t


def traite(chemin, table):
    im = Image.open(chemin).convert("RGBA")
    a = np.asarray(im, dtype=float).copy()
    rvb = a[..., :3]
    clair = np.clip((rvb.min(axis=2) - 120) / 100.0, 0, 1)

    masque = np.zeros(clair.shape, bool)
    poses = []
    for entree in table:
        yc, xc, en, fr = entree[:4]
        bornes = entree[4] if len(entree) > 4 else None
        mod = localise.gabarit(en, SEGOE, CORPS)
        h, w = mod.shape
        if bornes:
            gx0, gx1 = bornes
        else:
            gx0, gx1 = xc - w // 2 - 40, xc + w // 2 + 40
        fen = (max(0, yc - 9), min(clair.shape[0], yc + 9),
               max(0, gx0), min(clair.shape[1], gx1))
        s, y, x = localise.localise(clair, mod, fen)
        if s < 0.08:
            print("   !! %-26s introuvable (score %.2f)" % (en, s))
            continue
        Y0, Y1 = max(0, y - 5), min(masque.shape[0], y + h + 5)
        X0, X1 = fen[2], fen[3]
        masque[Y0:Y1, X0:X1] |= clair[Y0:Y1, X0:X1] > 0.10
        poses.append((y, x, mod, en, fr, s))

    gros = rebouche.dilate(masque, 4)
    neuf = rvb.copy()
    for y0, y1, x0, x1 in rebouche.blocs(gros):
        seul = np.zeros(gros.shape, bool)
        seul[y0:y1 + 1, x0:x1 + 1] = gros[y0:y1 + 1, x0:x1 + 1]
        neuf = rebouche.diffuse(neuf, seul, 300)
    rvb[:] = neuf

    for y, x, mod, en, fr, s in poses:
        modfr = localise.gabarit(fr, SEGOE, CORPS)
        cx = x + mod.shape[1] / 2.0
        xf = int(round(cx - modfr.shape[1] / 2.0))
        yf = y + (mod.shape[0] - modfr.shape[0])
        dessine(rvb, modfr, yf, max(0, xf), (255, 255, 255), (40, 25, 35))
        print("   %-26s -> %-24s %3d px (anglais %3d) score %.2f"
              % (en, fr, modfr.shape[1], mod.shape[1], s))

    a[..., :3] = np.clip(rvb, 0, 255)
    return Image.fromarray(a.astype("uint8"), "RGBA")


def reference(nom):
    dossier = os.path.join(DEPOT, "cg", "reference")
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    c = os.path.join(dossier, nom)
    if not os.path.exists(c):
        f = io.open(REFERENCE, "rb")
        T = dict((e.nom, e) for e in mpk.lit_table(f) if e.nom)
        io.open(c, "wb").write(mpk.lit(f, T[nom]))
    return c


def main():
    vises = [a for a in sys.argv[1:] if not a.startswith("--")]
    noms = [n for n in TABLES if not vises or any(v in n for v in vises)]
    faits = []
    for nom in sorted(noms):
        print(nom)
        im = traite(reference(nom), TABLES[nom])
        c = os.path.join(SORTIE, nom)
        im.save(c, optimize=True, compress_level=9)
        faits.append(c)
    if "--install" in sys.argv and faits:
        print()
        remplace.remplace(JEU + "c0data.mpk", faits)


if __name__ == "__main__":
    main()
