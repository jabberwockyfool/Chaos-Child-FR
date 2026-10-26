# -*- coding: utf-8 -*-
"""Onglets de l'interface du jeu en ligne (cc_pbg039a).

Le panneau est trame comme un ecran : motif de 3 rangees sur 2 colonnes qui
multiplie tout ce qui est dessine, texte compris. Le fond d'un onglet est donc
**constant le long de x** a parite donnee : il suffit de le relire dans une
colonne sans texte pour l'effacer exactement, sans rien inventer.

Le francais est ensuite pose avec la meme modulation : pour chaque rangee, on
reprend la valeur de crete des lettres d'origine, ce qui redonne les rayures.

Onglets : TALK -> CHAT, BATTLE -> COMBAT, EVENT -> EVENT (les trois tiennent
dans leur cellule, bornee par les separateurs ; PARLER et EVENEMENT, eux,
debordaient).

    python cg/outils/mmo.py [--install]
"""
import io
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

RACINE = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.dirname(os.path.dirname(RACINE))
sys.path.insert(0, RACINE)
import mpk          # noqa: E402
import remplace     # noqa: E402

JEU = "D:/SteamLibrary/steamapps/common/CHAOS;CHILD/languagebarrier/"
REFERENCE = JEU + "backup0data.mpk"
SORTIE = os.path.join(DEPOT, "cg", "c0data")
ETROITE_GRASSE = "C:/Windows/Fonts/impact.ttf"   # tres condense, comme l'original
CORPS = 23

NOM = "cc_pbg039a.png"

# (bande du texte, cellule bornee par les separateurs, colonne propre,
#  anglais, francais) ; le francais est centre dans sa cellule
ONGLETS = [
    ((693, 711), (112, 185), (176, 184), "TALK", "CHAT"),
    ((693, 711), (188, 272), (267, 271), "BATTLE", "COMBAT"),
    ((693, 711), (275, 355), (341, 353), "EVENT", "EVENT"),
]


def couverture(texte, corps=CORPS):
    ft = ImageFont.truetype(ETROITE_GRASSE, corps)
    img = Image.new("L", (400, 60), 0)
    ImageDraw.Draw(img).text((10, 10), texte, 255, font=ft)
    a = np.asarray(img, dtype=float) / 255.0
    ys, xs = np.nonzero(a > 0.5)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def traite(chemin):
    im = Image.open(chemin).convert("RGBA")
    a = np.asarray(im, dtype=float).copy()
    rvb = a[..., :3]

    for (y0, y1), (x0, x1), (cx0, cx1), en, fr in ONGLETS:
        # le fond, relu dans une colonne sans texte, parite par parite
        fond = np.zeros((y1 - y0, 2, 3))
        for p in (0, 1):
            cols = [x for x in range(cx0, cx1) if x % 2 == p]
            fond[:, p] = rvb[y0:y1, cols].mean(axis=1)

        # la crete des lettres d'origine, rangee par rangee
        bande = rvb[y0:y1, x0:x1]
        attendu = fond[:, np.arange(x0, x1) % 2]
        ecart = (bande - attendu).max(axis=2)
        crete = np.zeros((y1 - y0, 3))
        for i in range(y1 - y0):
            vifs = bande[i][ecart[i] > 0.6 * max(1.0, ecart[i].max())]
            crete[i] = vifs.mean(axis=0) if len(vifs) else attendu[i].mean(axis=0)

        # on repose le fond, puis le francais
        xs = np.arange(x0, x1)
        rvb[y0:y1, x0:x1] = fond[:, xs % 2]
        cov = couverture(fr)
        h, w = cov.shape
        if h > y1 - y0:
            cov = cov[:y1 - y0]
            h = cov.shape[0]
        yy = y0 + ((y1 - y0) - h) // 2
        xx = x0 + ((x1 - x0) - w) // 2
        for i in range(h):
            ligne = cov[i][:, None]
            cible = crete[min(yy - y0 + i, crete.shape[0] - 1)]
            bloc = rvb[yy + i, xx:xx + w]
            bloc[:] = bloc * (1 - ligne) + cible * ligne
        print("   %-7s -> %-7s  %2d px (anglais %2d), cellule %d px"
              % (en, fr, w, x1 - x0, x1 - x0))

    a[..., :3] = np.clip(rvb, 0, 255)
    return Image.fromarray(a.astype("uint8"), "RGBA")


def reference():
    dossier = os.path.join(DEPOT, "cg", "reference")
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    c = os.path.join(dossier, NOM)
    if not os.path.exists(c):
        f = io.open(REFERENCE, "rb")
        T = dict((e.nom, e) for e in mpk.lit_table(f) if e.nom)
        io.open(c, "wb").write(mpk.lit(f, T[NOM]))
    return c


def main():
    print(NOM)
    im = traite(reference())
    c = os.path.join(SORTIE, NOM)
    im.save(c, optimize=True, compress_level=9)
    if "--install" in sys.argv:
        print()
        remplace.remplace(JEU + "c0data.mpk", [c])


if __name__ == "__main__":
    main()
