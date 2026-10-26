# -*- coding: utf-8 -*-
"""mapbg : le plan de Shibuya punaise sur le liege.

On traduit le cartouche (Shibuya Station / 2015 Vers. / SURROUNDING AREA MAP)
et l'indication du nord. "2015 Vers." reste : l'abreviation est la meme.

La police du cartouche est Montserrat Bold (licence SIL OFL). Elle n'est pas
livree avec Windows : on la cherche dans cg/outils/polices/, dans les polices
de Windows et de l'utilisateur, puis dans les logiciels qui l'embarquent.
"""
import glob
import os

import numpy as np

import habillage
import rebouche

RACINE = os.path.dirname(os.path.abspath(__file__))


def police(nom):
    lieux = [os.path.join(RACINE, "polices", nom),
             os.path.join("C:/Windows/Fonts", nom),
             os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/" + nom)]
    lieux += glob.glob("C:/Program Files*/*/Versions/*/content/fonts/" + nom)
    for p in lieux:
        if os.path.exists(p):
            return p
    raise IOError("police introuvable : %s (a deposer dans %s)"
                  % (nom, os.path.join(RACINE, "polices")))


def gomme(a, zone):
    """Gomme l'encre noire d'une ligne du cartouche, par diffusion du papier ;
    rend la boite de l'encre et sa couleur."""
    y0, y1, x0, x1 = zone
    z = a[y0:y1, x0:x1]
    noir = z[..., :3].max(axis=2) < 140
    ys, xs = np.nonzero(z[..., :3].max(axis=2) < 100)
    boite = (y0 + ys.min(), y0 + ys.max(), x0 + xs.min(), x0 + xs.max())
    couleur = np.median(z[z[..., :3].max(axis=2) < 70][:, :3], axis=0)
    z[..., :3] = rebouche.diffuse(z[..., :3], rebouche.dilate(noir, 1), 300)
    return boite, couleur


def pose(a, boite, couleur, en, fr, police_, largeur_max, monte=0):
    g, y, x = habillage.comme(en, fr, police_, boite, largeur_max=largeur_max)
    y -= monte
    h, w = g.shape
    b = a[y:y + h, x:x + w, :3]
    b[:] = b * (1 - g[..., None]) + couleur * g[..., None]
    print("   %-20s -> %-18s %3d px (anglais %3d, place %3d)"
          % (en, fr, w, boite[3] - boite[2] + 1, largeur_max))
    return g, y, x


def deplace(a, zone, dy):
    """Deplace verticalement l'encre rouge de `zone`, sur le papier blanc."""
    y0, y1, x0, x1 = zone
    z = a[y0:y1, x0:x1]
    encre = z[..., :3].min(axis=2) < 200
    copie = z[..., :3].copy()
    z[..., :3] = rebouche.diffuse(z[..., :3], rebouche.dilate(encre, 1), 200)
    papier = z[..., :3].copy()
    # l'encre est posee comme un melange avec le papier : on reporte l'ecart
    ecart = copie - papier
    ys, xs = np.nonzero(rebouche.dilate(encre, 1))
    a[y0 + ys + dy, x0 + xs, :3] = np.clip(
        a[y0 + ys + dy, x0 + xs, :3] + ecart[ys, xs], 0, 255)


def plan(a):
    mont = police("Montserrat-Bold.ttf")
    # le cartouche : filet interieur de x 181 a 505 ; "2015 Vers." en rouge
    # a droite de la deuxieme ligne, de x 416 a 466
    zones = [(166, 228, 200, 480), (228, 284, 200, 414), (286, 309, 200, 480)]
    gommes = [gomme(a, z) for z in zones]
    # la queue du y de Shibuya (Station n'en avait pas) descend jusqu'a la
    # troisieme ligne : on remonte la deuxieme de 6 px, "2015 Vers." avec
    # elle (meme ligne de base), et la premiere de 4 px pour l'interligne
    pose(a, gommes[0][0], gommes[0][1], "Shibuya", "Gare de", mont, 467 - 214, monte=4)
    pose(a, gommes[1][0], gommes[1][1], "Station", "Shibuya", mont, 412 - 214, monte=6)
    deplace(a, (232, 284, 414, 470), -6)
    pose(a, gommes[2][0], gommes[2][1], "SURROUNDING AREA MAP", "PLAN DES ENVIRONS",
         mont, 467 - 214)
    # la rose des vents ; les noms de lieux du plan restent, en romaji
    habillage.panneau(a, (145, 167, 2422, 2474), "North", "Nord", False, (1, 14),
                      police="C:/Windows/Fonts/segoeui.ttf", large=30)
    return a
