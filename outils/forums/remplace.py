# -*- coding: utf-8 -*-
"""Remplace le contenu d'une entree d'archive MPK, sur place.

Les donnees sont alignees sur 2048 octets : tant que le nouveau contenu tient
dans le creneau de l'ancien, on ecrit par-dessus et on met a jour les deux
tailles de la table. Aucun decalage, le reste de l'archive est intact.
"""
import struct, sys, os
import mpk


def remplace(archive, nom, fichier):
    f, ver, entrees = mpk.lire(archive)
    f.close()
    cible = next((i, e) for i, e in enumerate(entrees) if e["nom"] == nom)
    i, e = cible
    donnees = open(fichier, "rb").read()
    creneau = -(-e["reel"] // mpk.ALIGNEMENT) * mpk.ALIGNEMENT
    if len(donnees) > creneau:
        raise SystemExit("trop gros : %d octets pour un creneau de %d"
                         % (len(donnees), creneau))
    with open(archive, "r+b") as a:
        a.seek(e["offset"])
        a.write(donnees)
        a.write(b"\0" * (creneau - len(donnees)))
        # tailles compressee et reelle dans la table
        a.seek(mpk.ENTETE + i * mpk.TAILLE_ENTREE + 16)
        a.write(struct.pack("<QQ", len(donnees), len(donnees)))
    print("%s : %s remplace (%d -> %d octets, creneau %d)"
          % (os.path.basename(archive), nom, e["reel"], len(donnees), creneau))


if __name__ == "__main__":
    remplace(sys.argv[1], sys.argv[2], sys.argv[3])
