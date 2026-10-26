# -*- coding: utf-8 -*-
"""Lecture d'une archive MPK de CHAOS;CHILD.

Entete 0x40 : "MPK\0", version, nombre d'entrees (u64 @0x8).
Table : 0x100 par entree a partir de 0x40 — compression u32, identifiant u32,
offset u64, taille compressee u64, taille reelle u64, puis le nom en ASCII.
Les donnees ne sont pas compressees et sont alignees sur 2 Ko.
"""
import struct


class Entree(object):
    __slots__ = ("i", "compression", "id", "offset", "csize", "usize", "nom")

    def __repr__(self):
        return "<%s %d o @%d>" % (self.nom, self.usize, self.offset)


def lit_table(f):
    f.seek(0)
    sig = f.read(4)
    if sig != b"MPK\0":
        raise ValueError("ce n'est pas un MPK : %r" % sig)
    f.seek(8)
    n = struct.unpack("<Q", f.read(8))[0]
    out = []
    for i in range(n):
        f.seek(0x40 + i * 0x100)
        bloc = f.read(0x100)
        e = Entree()
        e.i = i
        e.compression, e.id = struct.unpack("<II", bloc[:8])
        e.offset, e.csize, e.usize = struct.unpack("<QQQ", bloc[8:32])
        e.nom = bloc[32:].split(b"\0")[0].decode("ascii", "replace")
        out.append(e)
    return out


def lit(f, e):
    f.seek(e.offset)
    return f.read(e.usize)
