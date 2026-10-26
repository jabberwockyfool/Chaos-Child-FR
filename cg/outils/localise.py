# -*- coding: utf-8 -*-
"""Retrouve un texte anglais dans une image, par correlation.

On rend le texte au gabarit, puis on cherche ou il se superpose le mieux a
l'encre de l'image. Le score soustrait l'encre du **pourtour** du gabarit :
sans ca, une grande tache claire du decor (un nuage, le contour d'un dessin)
l'emporte sur les lettres.

La correlation passe par la transformee de Fourier : balayer 1920 x 1080 pour
une quinzaine de libelles serait sinon interminable.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import rebouche


def gabarit(texte, police, corps):
    ft = ImageFont.truetype(police, corps)
    img = Image.new("L", (900, 60), 0)
    ImageDraw.Draw(img).text((10, 10), texte, 255, font=ft)
    a = np.asarray(img)
    ys, xs = np.nonzero(a > 128)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1] > 128


def _correle(poids, modele):
    """Somme de `poids` sous le gabarit, pour toutes les positions."""
    h, w = poids.shape
    th, tw = modele.shape
    n0 = 1 << int(np.ceil(np.log2(h + th)))
    n1 = 1 << int(np.ceil(np.log2(w + tw)))
    A = np.fft.rfft2(poids, s=(n0, n1))
    B = np.fft.rfft2(modele[::-1, ::-1].astype(float), s=(n0, n1))
    c = np.fft.irfft2(A * B, s=(n0, n1))
    return c[th - 1:th - 1 + h - th + 1, tw - 1:tw - 1 + w - tw + 1]


def localise(poids, modele, fenetre=None):
    """Meilleure position du gabarit, et son score.

    `poids` vaut 1 la ou le pixel a la couleur du texte. Le score vaut 1 pour
    un recouvrement parfait avec un pourtour vide ; les lettres etant
    anticrenelees, 0,2 suffit deja a designer la bonne position.
    """
    anneau = (rebouche.dilate(modele, 2) & ~modele)
    if fenetre:
        y0, y1, x0, x1 = fenetre
        p = poids[y0:y1, x0:x1]
    else:
        y0, x0 = 0, 0
        p = poids
    a = _correle(p, modele) / float(modele.sum())
    b = _correle(p, anneau) / float(max(1, anneau.sum()))
    s = a - b
    i = int(np.argmax(s))
    y, x = divmod(i, s.shape[1])
    return float(s[y, x]), y + y0, x + x0
