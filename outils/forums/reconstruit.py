# -*- coding: utf-8 -*-
"""Reconstruit une archive MPK en remplacant le contenu de certaines entrees.

Sert quand le nouveau fichier ne tient plus dans le creneau de l'ancien : on
reecrit l'archive entiere, en recalculant les offsets (alignes sur 2048). Les
entrees non remplacees sont recopiees octet pour octet depuis l'original.
"""
import os, struct, sys
import mpk


def reconstruit(source, destination, remplacements, dossier):
    """remplacements : noms d'entrees a relire depuis <dossier>"""
    f, ver, entrees = mpk.lire(source)
    n = len(entrees)
    debut = min(e["offset"] for e in entrees if e["reel"] > 0)

    with open(destination, "wb") as out:
        out.write(b"MPK\0")
        out.write(struct.pack("<HHI", ver[0], ver[1], n))
        out.write(b"\0" * (mpk.ENTETE - 12))
        out.write(b"\0" * (debut - mpk.ENTETE))     # place pour la table

        offsets = []
        for e in entrees:
            if e["nom"] in remplacements:
                donnees = open(os.path.join(dossier, e["nom"]), "rb").read()
            elif e["reel"] == 0:
                donnees = b""
            else:
                f.seek(e["offset"])
                donnees = f.read(e["reel"])
            pos = out.tell()
            out.write(donnees)
            reste = (-len(donnees)) % mpk.ALIGNEMENT
            out.write(b"\0" * reste)
            offsets.append((pos if donnees else e["offset"], len(donnees)))

        # table des matieres
        out.seek(mpk.ENTETE)
        for e, (pos, taille) in zip(entrees, offsets):
            out.write(struct.pack("<II", e["cle"], e["id"]))
            out.write(struct.pack("<QQQ", pos, taille, taille))
            nom = e["nom"].encode("utf-8")
            out.write(nom + b"\0" * (224 - len(nom)))
    f.close()
    print("%s : %d entrees, %d remplacees" % (os.path.basename(destination),
                                              n, len(remplacements)))


if __name__ == "__main__":
    src, dst, dossier = sys.argv[1], sys.argv[2], sys.argv[3]
    reconstruit(src, dst, set(sys.argv[4:]), dossier)
