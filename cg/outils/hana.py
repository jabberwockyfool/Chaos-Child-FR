# -*- coding: utf-8 -*-
"""Les onze repliques de tchat des calques CC_HANA_*.

Chaque ligne donne l'anglais d'origine et sa traduction. L'anglais sert de
gabarit : c'est sur lui que sont mesures le corps et l'espacement, pour que le
francais sorte a la meme taille que ce qu'il remplace.

Un segment entre crochets est colorie en cyan, comme dans les variantes _B.

    python cg/outils/hana.py            # ecrit les PNG dans cg/c0data/
    python cg/outils/hana.py --install  # et les pose dans l'archive du jeu
"""
import io
import os
import sys

RACINE = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.dirname(os.path.dirname(RACINE))
sys.path.insert(0, RACINE)
import mpk            # noqa: E402
import remplace       # noqa: E402
import surimpression as S  # noqa: E402

REFERENCE = ("D:/SteamLibrary/steamapps/common/CHAOS;CHILD/languagebarrier"
             "/backup0data.mpk")
SORTIE = os.path.join(DEPOT, "cg", "c0data")

G, D, A = "\u201c", "\u201d", "\u2019"   # guillemets et apostrophe des scripts

LIGNES = [
    ("CC_HANA_001.png", "Flame magic!", "Magie de feu !"),
    ("CC_HANA_002.png", "Ice magic!", "Magie de glace !"),
    ("CC_HANA_003.png", "Lightning magic!", "Magie de foudre !"),
    ("CC_HANA_004.png",
     "That one hero that%ss never logged out since launch!" % A,
     "Le h\u00e9ros qui s%sest jamais d\u00e9connect\u00e9 depuis la sortie !" % A),
    ("CC_HANA_005.png",
     "That addict who%ss maxed all the classes!" % A,
     "L%saccro qui a mont\u00e9 toutes les classes \u00e0 fond !" % A),
    # le lisere y est plus epais que sur les autres, d'ou son air gras
    ("CC_HANA_006.png", "Lightning-Fast Neidhardt!",
     "Neidhardt l%s\u00c9clair !" % A, (1, 1.5, 1.5)),
    ("CC_HANA_007.png", "Sister Centipede!", "S\u0153ur Scolopendre !"),
    ("CC_HANA_008_A.png", "Cheat code!", "Cheat code !"),
    ("CC_HANA_008_B.png", "Cheat code!", "[Cheat] code !"),
    ("CC_HANA_009_A.png", "Account ban!", "Ban de compte !"),
    ("CC_HANA_009_B.png", "Account ban!", "[Ban] de compte !"),
]


def references(noms):
    """Sort les calques anglais de l'archive de reference, pour servir de gabarit."""
    dossier = os.path.join(DEPOT, "cg", "reference")
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    f = io.open(REFERENCE, "rb")
    T = dict((e.nom, e) for e in mpk.lit_table(f) if e.nom)
    for n in noms:
        c = os.path.join(dossier, n)
        if not os.path.exists(c):
            io.open(c, "wb").write(mpk.lit(f, T[n]))
    return dossier


def main():
    ref = references([l[0] for l in LIGNES])
    if not os.path.isdir(SORTIE):
        os.makedirs(SORTIE)
    faits = []
    for ligne in LIGNES:
        nom, en, fr = ligne[:3]
        lisere = ligne[3] if len(ligne) > 3 else None
        im, m, taille, ch, larg, x = S.compose(os.path.join(ref, nom),
                                               G + en + D, G + fr + D,
                                               S.POLICE, lisere)
        chemin = os.path.join(SORTIE, nom)
        im.save(chemin, optimize=True, compress_level=9)
        faits.append(chemin)
        print("%-18s corps %2d  espacement %+5.2f  %4d px (anglais %4d)  x=%4d"
              % (nom, taille, ch, larg, m["largeur"], x))
    if "--install" in sys.argv:
        cible = ("D:/SteamLibrary/steamapps/common/CHAOS;CHILD/languagebarrier"
                 "/c0data.mpk")
        print()
        remplace.remplace(cible, faits)


if __name__ == "__main__":
    main()
