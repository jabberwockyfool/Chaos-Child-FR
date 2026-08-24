# -*- coding: utf-8 -*-
"""Lecture / ecriture d'une archive MPK (moteur SC3).

En-tete 0x40 : magic "MPK\0", version, nombre d'entrees.
Table a 0x40, 0x100 octets par entree : id, offset, taille compressee,
taille reelle, puis le nom sur 224 octets. Donnees alignees sur 2048.
"""
import struct, sys, os

ENTETE = 0x40
TAILLE_ENTREE = 0x100
ALIGNEMENT = 2048


def lire(chemin):
    f = open(chemin, "rb")
    magic = f.read(4)
    assert magic == b"MPK\0", magic
    v1, v2, n = struct.unpack("<HHI", f.read(8))
    entrees = []
    for i in range(n):
        f.seek(ENTETE + i * TAILLE_ENTREE)
        cle, ident = struct.unpack("<II", f.read(8))
        offset, taille_c, taille_r = struct.unpack("<QQQ", f.read(24))
        nom = f.read(224).split(b"\0")[0].decode("utf-8", "replace")
        entrees.append({"cle": cle, "id": ident, "offset": offset,
                        "compresse": taille_c, "reel": taille_r, "nom": nom})
    return f, (v1, v2), entrees


if __name__ == "__main__":
    f, ver, e = lire(sys.argv[1])
    print("version", ver, "entrees", len(e))
    for x in e[:5]:
        print(x)
    print("...")
    noms = set(x["nom"] for x in e)
    if len(sys.argv) > 2:
        dossier = sys.argv[2]
        fichiers = set(os.listdir(dossier))
        print("fichiers du dossier absents de l'archive :",
              sorted(fichiers - noms)[:10], len(fichiers - noms))
        print("entrees de l'archive absentes du dossier :", len(noms - fichiers))
