# -*- coding: utf-8 -*-
"""Lecture et ecriture des textures .dds du jeu.

Les 28 textures de `c0data.mpk` sont en DXT1 ou DXT5, sans mipmap, avec une
entete de 128 octets. Pillow les lit mais ne sait les reecrire que non
compressees (quatre fois trop gros) : on passe donc par `quicktex`, qui encode
le BC1 et le BC3.

Un bloc compresse a une taille fixe, donc la texture reencodee fait exactement
le poids de l'originale et rentre toujours dans le creneau du MPK.

Et comme la compression se fait par blocs de 4 x 4 independants, on ne
reencode que les blocs reellement touches : partout ailleurs on recopie les
octets d'origine, et la perte est nulle.
"""
import io
import struct

import numpy as np
import quicktex
import quicktex.s3tc.bc1 as bc1
import quicktex.s3tc.bc3 as bc3

ENTETE = 128


def format_de(chemin):
    d = io.open(chemin, "rb").read(ENTETE)
    if d[:4] != b"DDS ":
        raise ValueError("%s n'est pas un DDS" % chemin)
    h = struct.unpack("<I", d[12:16])[0]
    w = struct.unpack("<I", d[16:20])[0]
    return d[84:88].decode("ascii", "replace").strip("\0"), w, h


def lit(chemin):
    """Rend (entete, fourcc, largeur, hauteur, donnees compressees, RGBA)."""
    brut = io.open(chemin, "rb").read()
    fourcc, w, h = format_de(chemin)
    donnees = brut[ENTETE:]
    T = bc1.BC1Texture if fourcc == "DXT1" else bc3.BC3Texture
    D = bc1.BC1Decoder() if fourcc == "DXT1" else bc3.BC3Decoder()
    taille = (w // 4) * (h // 4) * (8 if fourcc == "DXT1" else 16)
    rgba = np.frombuffer(D.decode(T.from_bytes(donnees[:taille], w, h)).tobytes(),
                         dtype="uint8").reshape(h, w, 4).copy()
    return dict(entete=brut[:ENTETE], fourcc=fourcc, w=w, h=h,
                donnees=donnees, taille=taille, rgba=rgba)


def _transparent(bloc):
    """Un bloc DXT1 a trois couleurs (c0 <= c1) dont un pixel prend l'indice
    3 : ce pixel est transparent."""
    c0, c1, indices = struct.unpack("<HHI", bloc)
    return c0 <= c1 and any((indices >> (2 * k)) & 3 == 3 for k in range(16))


def ecrit(chemin, t, rgba):
    """Reecrit la texture, en ne reencodant que les blocs 4 x 4 modifies."""
    w, h, fourcc = t["w"], t["h"], t["fourcc"]
    enc = (bc1.BC1Encoder(level=18) if fourcc == "DXT1"
           else bc3.BC3Encoder(level=18))
    octets = 8 if fourcc == "DXT1" else 16
    rt = quicktex.RawTexture.frombytes(np.ascontiguousarray(rgba).tobytes(), w, h)
    neuf = enc.encode(rt).tobytes()

    # quels blocs ont bouge ?
    bouge = (np.abs(rgba.astype(int) - t["rgba"].astype(int)).max(axis=2) > 0)
    bw, bh = w // 4, h // 4
    par_bloc = bouge[:bh * 4, :bw * 4].reshape(bh, 4, bw, 4).any(axis=(1, 3))

    sortie = bytearray(t["donnees"][:t["taille"]])
    n = 0
    for by, bx in zip(*np.nonzero(par_bloc)):
        i = (by * bw + bx) * octets
        if fourcc == "DXT1" and (_transparent(t["donnees"][i:i + 8])
                                 or _transparent(neuf[i:i + 8])):
            raise ValueError("bloc DXT1 (%d, %d) transparent : quicktex ne lit ni n'ecrit "
                             "cette transparence" % (bx * 4, by * 4))
        sortie[i:i + octets] = neuf[i:i + octets]
        n += 1
    reste = t["donnees"][t["taille"]:]
    io.open(chemin, "wb").write(t["entete"] + bytes(sortie) + reste)
    return n, bw * bh
