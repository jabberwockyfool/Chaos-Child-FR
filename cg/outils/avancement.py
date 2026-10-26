# -*- coding: utf-8 -*-
"""Ou en est la traduction des images ?

Compare l'archive installee dans le jeu a la reference anglaise du Committee of
Zero. Une entree qui en differe a ete retouchee par l'equipe ; une entree
identique est restee en anglais.

`c0data.mpk` est l'archive de surcharge du patch anglais : elle ne contient que
des fichiers que le Committee of Zero a eu besoin de refaire, donc des images
porteuses de texte. Ce qui n'a pas ete retouche est encore en anglais a l'ecran.

    python cg/outils/avancement.py
    python cg/outils/avancement.py --liste      # les noms, pas seulement le compte
    python cg/outils/avancement.py --extrait D  # ecrit les PNG restants dans D
"""
import hashlib
import io
import os
import sys

RACINE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RACINE)
import mpk  # noqa: E402

JEU = "D:/SteamLibrary/steamapps/common/CHAOS;CHILD/languagebarrier/"
INSTALLE = JEU + "c0data.mpk"
REFERENCE = JEU + "backup0data.mpk"   # mis de cote par LanguageBarrier


def table(chemin):
    f = io.open(chemin, "rb")
    return f, dict((e.nom, e) for e in mpk.lit_table(f) if e.nom)


def compare():
    fr_f, FR = table(INSTALLE)
    en_f, EN = table(REFERENCE)
    faits, restants = [], []
    for nom in sorted(FR):
        if nom not in EN:
            faits.append(nom)
            continue
        a = hashlib.sha1(mpk.lit(en_f, EN[nom])).hexdigest()
        b = hashlib.sha1(mpk.lit(fr_f, FR[nom])).hexdigest()
        (faits if a != b else restants).append(nom)
    return fr_f, FR, faits, restants


def main():
    fr_f, FR, faits, restants = compare()
    total = len(FR)
    print("%d entrees dans l'archive" % total)
    print("  traduites : %3d  (%.0f %%)" % (len(faits), 100.0 * len(faits) / total))
    print("  restantes : %3d  (%.0f %%)" % (len(restants), 100.0 * len(restants) / total))
    if "--liste" in sys.argv:
        print("\nRestantes :")
        for n in restants:
            print("   ", n)
    if "--extrait" in sys.argv:
        dossier = sys.argv[sys.argv.index("--extrait") + 1]
        if not os.path.isdir(dossier):
            os.makedirs(dossier)
        for n in restants:
            io.open(os.path.join(dossier, n), "wb").write(mpk.lit(fr_f, FR[n]))
        print("\n%d fichiers ecrits dans %s" % (len(restants), dossier))


if __name__ == "__main__":
    main()
