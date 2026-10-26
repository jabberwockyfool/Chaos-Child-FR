# -*- coding: utf-8 -*-
"""Rebouche un trou dans une image en recopiant le meilleur morceau voisin.

Pour chaque trou, on cherche le decalage (dy, dx) qui fait le mieux coincider
le pourtour du trou avec le reste de l'image, puis on recopie la zone decalee.
Sur un fond a motif, le decalage trouve est la periode du motif ; sur un fond
lisse, c'est un voisin quelconque, ce qui revient au meme. Aucune invention :
on ne pose que des pixels qui existent deja ailleurs dans l'image.
"""
import numpy as np
from PIL import Image, ImageFilter


def dilate(m, r):
    im = Image.fromarray((m * 255).astype("uint8"))
    for _ in range(r):
        im = im.filter(ImageFilter.MaxFilter(3))
    return np.asarray(im) > 127


def blocs(m):
    """Les composantes du masque, par balayage (sans scipy)."""
    vus = np.zeros(m.shape, bool)
    out = []
    ys, xs = np.nonzero(m)
    for y0, x0 in zip(ys, xs):
        if vus[y0, x0]:
            continue
        pile = [(y0, x0)]
        vus[y0, x0] = True
        hy = [y0, y0]
        hx = [x0, x0]
        while pile:
            y, x = pile.pop()
            hy[0] = min(hy[0], y); hy[1] = max(hy[1], y)
            hx[0] = min(hx[0], x); hx[1] = max(hx[1], x)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    v, u = y + dy, x + dx
                    if 0 <= v < m.shape[0] and 0 <= u < m.shape[1] \
                            and m[v, u] and not vus[v, u]:
                        vus[v, u] = True
                        pile.append((v, u))
        out.append((hy[0], hy[1], hx[0], hx[1]))
    return out


def rebouche(img, masque, portee=140, marge=4):
    """img : tableau (h, w, c) ; masque : la zone a refaire."""
    a = img.astype(float).copy()
    trous = blocs(masque)
    # on regroupe les trous proches, sinon on cherche un decalage par lettre
    fusion = []
    for y0, y1, x0, x1 in trous:
        for f in fusion:
            if y0 <= f[1] + 6 and y1 >= f[0] - 6 and x0 <= f[3] + 10 and x1 >= f[2] - 10:
                f[0] = min(f[0], y0); f[1] = max(f[1], y1)
                f[2] = min(f[2], x0); f[3] = max(f[3], x1)
                break
        else:
            fusion.append([y0, y1, x0, x1])

    h, w = masque.shape
    for y0, y1, x0, x1 in fusion:
        Y0, Y1 = max(0, y0 - marge), min(h, y1 + 1 + marge)
        X0, X1 = max(0, x0 - marge), min(w, x1 + 1 + marge)
        trou = masque[Y0:Y1, X0:X1]
        bord = dilate(trou, marge) & ~trou
        if not bord.any():
            continue
        ref = a[Y0:Y1, X0:X1]
        best = None
        for dy in range(-portee, portee + 1, 1):
            for dx in range(-portee, portee + 1, 1):
                if abs(dy) < Y1 - Y0 and abs(dx) < X1 - X0:
                    continue          # chevauche le trou lui-meme
                sy0, sx0 = Y0 + dy, X0 + dx
                if sy0 < 0 or sx0 < 0 or sy0 + (Y1 - Y0) > h or sx0 + (X1 - X0) > w:
                    continue
                if masque[sy0:sy0 + (Y1 - Y0), sx0:sx0 + (X1 - X0)].any():
                    continue          # la source doit etre propre
                src = a[sy0:sy0 + (Y1 - Y0), sx0:sx0 + (X1 - X0)]
                d = np.abs(src[bord] - ref[bord]).mean()
                if best is None or d < best[0]:
                    best = (d, dy, dx)
        if best is None:
            continue
        _, dy, dx = best
        src = a[Y0 + dy:Y0 + dy + (Y1 - Y0), X0 + dx:X0 + dx + (X1 - X0)]
        ref[trou] = src[trou]
    return a


def diffuse(img, masque, tours=400):
    """Rebouche en diffusant le pourtour (equation de Laplace).

    Contrairement a une interpolation en ligne ou en colonne, qui laisse des
    coulures des qu'un trait sombre touche le bord du trou, la diffusion
    moyenne les quatre voisins et ne privilegie aucune direction. Le detail
    fin est perdu a l'interieur du trou, mais un trou de texte est mince : le
    resultat se lit comme la continuation du fond.
    """
    a = img.astype(float).copy()
    m = masque.astype(bool)
    if not m.any():
        return a
    ys, xs = np.nonzero(m)
    y0, y1 = max(0, ys.min() - 2), min(a.shape[0], ys.max() + 3)
    x0, x1 = max(0, xs.min() - 2), min(a.shape[1], xs.max() + 3)
    z = a[y0:y1, x0:x1]
    t = m[y0:y1, x0:x1]
    # depart : moyenne du pourtour, pour converger plus vite
    bord = dilate(t, 1) & ~t
    if bord.any():
        z[t] = z[bord].mean(axis=0)
    for _ in range(tours):
        v = z.copy()
        v[1:-1, 1:-1] = 0.25 * (z[:-2, 1:-1] + z[2:, 1:-1]
                                + z[1:-1, :-2] + z[1:-1, 2:])
        z[t] = v[t]
    a[y0:y1, x0:x1] = z
    return a
