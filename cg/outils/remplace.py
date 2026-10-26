# -*- coding: utf-8 -*-
"""Remplace une entree dans un MPK sans reconstruire l'archive.

Les donnees ne sont pas compressees et chaque entree demarre sur un multiple de
2048. Tant que le nouveau fichier tient dans le creneau de l'ancien (celui-ci
va jusqu'au debut de l'entree suivante), on ecrit par-dessus a `offset` et on
met a jour les deux tailles dans la table. Rien ne bouge, le reste de l'archive
est intact.

    python cg/outils/remplace.py <archive.mpk> <fichier> [<fichier> ...]

Le nom du fichier doit etre celui de l'entree. Si le PNG ne tient pas, on le
re-enregistre compresse au maximum avant d'abandonner.
"""
import io
import os
import struct
import sys

from PIL import Image

RACINE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RACINE)
import mpk  # noqa: E402

ALIGN = 2048


def creneaux(entrees):
    """Place disponible pour chaque entree, jusqu'au debut de la suivante."""
    bornes = sorted(e.offset for e in entrees if e.nom)
    suivant = dict(zip(bornes, bornes[1:]))
    return suivant


def _png(im, pas=1):
    """Le PNG le plus court possible, sans changer de type de couleur."""
    import numpy as np
    if pas > 1:
        a = np.asarray(im, dtype=float)
        a = (np.clip(a / float(pas), 0, 255.0 / pas).round() * pas).clip(0, 255)
        im = Image.fromarray(a.astype("uint8"), im.mode)
    t = io.BytesIO()
    im.save(t, "PNG", optimize=True, compress_level=9)
    data = t.getvalue()
    try:
        import zopfli.png
        z = zopfli.png.optimize(data)
        # zopfli reduit le type de couleur quand il peut (RGBA -> niveaux de
        # gris). Les PNG du jeu ne sont que RGB ou RGBA : on ne lui fait pas
        # avaler un type qu'il n'a jamais eu a lire.
        if len(z) < len(data) and Image.open(io.BytesIO(z)).mode == im.mode:
            data = z
    except ImportError:
        pass
    return data


def serre(chemin, place):
    """Fait rentrer un PNG dans la place disponible.

    D'abord la seule compression ; si ca ne suffit pas, on arrondit les
    valeurs par paliers de plus en plus gros. A la taille ou ces images sont
    vues, 64 niveaux ne se distinguent pas de 256.
    """
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(chemin)
    if im.format != "PNG":
        return None
    for pas in (1, 2, 4, 8, 16, 32):
        data = _png(im, pas)
        if len(data) <= place:
            return data, pas
    return data, pas


def remplace(archive, fichiers, verbeux=True):
    f = io.open(archive, "r+b")
    table = mpk.lit_table(f)
    T = dict((e.nom, e) for e in table if e.nom)
    suivant = creneaux(table)
    fin = os.path.getsize(archive)

    for chemin in fichiers:
        nom = os.path.basename(chemin)
        if nom not in T:
            raise SystemExit("%s : pas d'entree de ce nom dans l'archive" % nom)
        e = T[nom]
        place = suivant.get(e.offset, fin) - e.offset
        data = io.open(chemin, "rb").read()
        if len(data) > place:
            r = serre(chemin, place)
            if r is None or len(r[0]) > place:
                raise SystemExit("%s : %d o pour %d disponibles, il faut alleger l'image"
                                 % (nom, len(data), place))
            if verbeux:
                print("   %s recomprime : %d -> %d o%s"
                      % (nom, len(data), len(r[0]),
                         "" if r[1] == 1 else " (valeurs arrondies au pas de %d)" % r[1]))
            data = r[0]
        f.seek(e.offset)
        f.write(data)
        reste = place - len(data)
        if reste:
            f.write(b"\0" * min(reste, ALIGN))   # on nettoie la queue de l'ancien
        f.seek(0x40 + e.i * 0x100 + 16)
        f.write(struct.pack("<QQ", len(data), len(data)))
        if verbeux:
            print("   %-28s %8d / %8d o" % (nom, len(data), place))
    f.close()


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    remplace(sys.argv[1], sys.argv[2:])
    print("fait")


if __name__ == "__main__":
    main()
