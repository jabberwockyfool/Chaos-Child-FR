# -*- coding: utf-8 -*-
"""Etiquettes du bureau Windows et titre d'onglet (cc_pbg005aa..fa).

Les six images sont le meme bureau : seuls l'horloge et deux details changent.
Le texte est du Segoe UI 12 px blanc avec une ombre portee sombre, pose sur un
papier peint charge. Plutot que de deviner ou est le texte au seuil (le decor
est blanc par endroits), on **reconnait l'anglais** : on rend l'etiquette au
gabarit et on la fait glisser dans sa fenetre jusqu'a ce qu'elle coincide. Le
masque obtenu colle donc exactement aux lettres.

Le trou est ensuite rebouche par recopie du meilleur morceau voisin
(`rebouche.py`), puis le francais est redessine au meme endroit.

    python cg/outils/bureau.py [--install]
"""
import io
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RACINE = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.dirname(os.path.dirname(RACINE))
sys.path.insert(0, RACINE)
import mpk          # noqa: E402
import rebouche     # noqa: E402
import remplace     # noqa: E402

JEU = "D:/SteamLibrary/steamapps/common/CHAOS;CHILD/languagebarrier/"
REFERENCE = JEU + "backup0data.mpk"
SORTIE = os.path.join(DEPOT, "cg", "c0data")
SEGOE = "C:/Windows/Fonts/segoeui.ttf"
CORPS = 12

CALQUES = ["cc_pbg005aa.png", "cc_pbg005ba.png", "cc_pbg005ca.png",
           "cc_pbg005da.png", "cc_pbg005ea.png", "cc_pbg005fa.png"]

# (fenetre de recherche, anglais, francais)
# Les noms de marque parodies (Internet Escape, HACHIBASE, iTumes, RINE,
# AfterAction, PhotoStore ELEMENT) restent tels quels, comme les enseignes.
ETIQUETTES = [
    ((84, 102, 25, 145), "Computer", "Ordinateur"),
    ((182, 199, 15, 150), "Recycle Bin", "Corbeille"),
    ((701, 717, 30, 140), "Shared", "Partagé"),
    ((721, 737, 30, 140), "- Shortcut", "- Raccourci"),
    ((812, 828, 30, 140), "Images", "Images"),
    ((828, 844, 30, 140), "- Shortcut", "- Raccourci"),
    ((812, 830, 135, 270), "New Genera...", "New Genera..."),
    ((828, 846, 135, 270), "- Shortcut", "- Raccourci"),
    ((978, 996, 1750, 1915), "For manager...", "Pour la direc..."),
    ((994, 1010, 1750, 1915), "-Shortcut", "-Raccourci"),
]

# le titre d'onglet du navigateur : texte sombre sur le fond clair de
# l'onglet, en Segoe UI Semibold 13 (releve par gabarit)
SEMIGRAS = "C:/Windows/Fonts/segoeuisl.ttf"
ONGLET = ((38, 64, 945, 1115), '@chan "News bulletin x" b...',
          '@chan "Bulletin info x" f...')


def gabarit(texte, police=SEGOE, corps=CORPS):
    ft = ImageFont.truetype(police, corps)
    img = Image.new("L", (600, 40), 0)
    ImageDraw.Draw(img).text((10, 5), texte, 255, font=ft)
    a = np.asarray(img)
    ys, xs = np.nonzero(a > 128)
    return (a[ys.min():ys.max() + 1, xs.min():xs.max() + 1] > 128)


def place(poids, modele, fenetre):
    """Position du gabarit qui recouvre le mieux l'encre de la fenetre.

    `poids` vaut 1 la ou le pixel est franchement de la couleur du texte, 0
    ailleurs, avec un degrade entre les deux : les lettres etant anticrenelees,
    un score parfait est hors d'atteinte et 0,5 veut deja dire « c'est la ».
    """
    y0, y1, x0, x1 = fenetre
    zone = poids[y0:y1, x0:x1]
    m = modele.astype(float)
    # le pourtour doit etre vide : sans ca, une grande tache claire du decor
    # (le contour blanc de l'ours) donne un meilleur score que le texte
    anneau = (rebouche.dilate(modele, 2) & ~modele).astype(float)
    h, w = modele.shape
    best = None
    for dy in range(0, max(1, zone.shape[0] - h + 1)):
        for dx in range(0, max(1, zone.shape[1] - w + 1)):
            bout = zone[dy:dy + h, dx:dx + w]
            if bout.shape != modele.shape:
                continue
            n = float((bout * m).sum() / m.sum()
                      - (bout * anneau).sum() / anneau.sum())
            if best is None or n > best[0]:
                best = (n, dy + y0, dx + x0)
    return best


def dessine(img, modele, y, x, couleur, ombre):
    """Repose une etiquette : l'ombre portee d'abord, la lettre ensuite."""
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


def traite(chemin):
    im = Image.open(chemin).convert("RGBA")
    a = np.asarray(im, dtype=float).copy()
    rvb = a[..., :3]
    clair = np.clip((rvb.min(axis=2) - 120) / 100.0, 0, 1)

    masque = np.zeros(clair.shape, bool)
    poses = []
    for fen, en, fr in ETIQUETTES:
        mod = gabarit(en)
        p = place(clair, mod, fen)
        if p is None or p[0] < 0.08:
            print("   !! %-16s introuvable dans %s" % (en, str(fen)))
            continue
        _, y, x = p
        # le gabarit donne l'emplacement ; le masque, lui, suit les pixels
        # reellement clairs de cette boite, a quelques pixels pres
        # le gabarit donne la ligne ; pour le masque on prend toute la
        # largeur de la fenetre, le calage au pixel pres n'etant pas acquis
        h, w = mod.shape
        Y0, Y1 = max(0, y - 4), min(masque.shape[0], y + h + 4)
        X0, X1 = fen[2], fen[3]
        masque[Y0:Y1, X0:X1] |= clair[Y0:Y1, X0:X1] > 0.10
        poses.append((y, x, mod, en, fr))

    # le titre d'onglet : texte sombre sur fond clair
    fen, en, fr = ONGLET
    y0, y1, x0, x1 = fen
    sombre = np.clip((110 - rvb.max(axis=2)) / 70.0, 0, 1)
    mod = gabarit(en, SEMIGRAS, 13)
    p = place(sombre, mod, fen)
    onglet = None
    if p and p[0] > 0.08:
        _, y, x = p
        h, w = mod.shape
        Y0, Y1 = max(0, y - 3), min(masque.shape[0], y + h + 3)
        X0, X1 = max(0, x - 3), min(masque.shape[1], x + w + 3)
        masque[Y0:Y1, X0:X1] |= sombre[Y0:Y1, X0:X1] > 0.20
        onglet = (y, x, en, fr)
    else:
        print("   !! onglet introuvable")

    gros = rebouche.dilate(masque, 4)
    # on rebouche trou par trou, en diffusant le pourtour
    neuf = rvb.copy()
    for y0, y1, x0, x1 in rebouche.blocs(gros):
        seul = np.zeros(gros.shape, bool)
        seul[y0:y1 + 1, x0:x1 + 1] = gros[y0:y1 + 1, x0:x1 + 1]
        neuf = rebouche.diffuse(neuf, seul, 300)
    rvb[:] = neuf

    for y, x, mod, en, fr in poses:
        modfr = gabarit(fr)
        # on garde le centre de l'etiquette d'origine
        cx = x + mod.shape[1] / 2.0
        xf = int(round(cx - modfr.shape[1] / 2.0))
        yf = y + (mod.shape[0] - modfr.shape[0])      # meme ligne de base
        dessine(rvb, modfr, yf, xf, (255, 255, 255), (40, 25, 35))
    if onglet:
        y, x, en, fr = onglet
        modfr = gabarit(fr, SEMIGRAS, 13)
        yf = y + (gabarit(en, SEMIGRAS, 13).shape[0] - modfr.shape[0])
        dessine(rvb, modfr, yf, x, (30, 30, 30), (225, 235, 245))

    a[..., :3] = np.clip(rvb, 0, 255)
    return Image.fromarray(a.astype("uint8"), "RGBA")


def references():
    dossier = os.path.join(DEPOT, "cg", "reference")
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    f = io.open(REFERENCE, "rb")
    T = dict((e.nom, e) for e in mpk.lit_table(f) if e.nom)
    for n in CALQUES:
        c = os.path.join(dossier, n)
        if not os.path.exists(c):
            io.open(c, "wb").write(mpk.lit(f, T[n]))
    return dossier


def main():
    ref = references()
    faits = []
    for n in CALQUES:
        print(n)
        im = traite(os.path.join(ref, n))
        c = os.path.join(SORTIE, n)
        im.save(c, optimize=True, compress_level=9)
        faits.append(c)
    if "--install" in sys.argv:
        print()
        remplace.remplace(JEU + "c0data.mpk", faits)


if __name__ == "__main__":
    main()
