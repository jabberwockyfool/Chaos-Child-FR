# -*- coding: utf-8 -*-
"""Decoupe une page de forum @chan de CHAOS;CHILD en lignes de texte.

Une page fait 1292 de large : cadre orange, fond `#EEEEEE`, un en-tete par
message (numero, « Name : », pseudo vert, « Submitted », ID) puis les lignes du
corps en noir. Le titre du fil est en rouge.

Convention du projet (voir les deux pages deja traduites) : on ne traduit que le
**titre** et le **corps** des messages ; les en-tetes restent en anglais.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FOND = (238, 238, 238)
ENCRE = (0, 0, 0)
POLICE = "C:/Windows/Fonts/segoeuib.ttf"
TAILLE = 18


def charge(chemin):
    return Image.open(chemin).convert("RGB")


def bandes(im, x0=30, x1=1265, seuil=170):
    """bandes horizontales contenant de l'encre, avec leur etendue en x"""
    a = np.array(im.convert("L"), dtype=np.int16)[:, x0:x1]
    lignes = (a < seuil).sum(axis=1) > 0
    out, deb = [], None
    for y, v in enumerate(lignes):
        if v and deb is None:
            deb = y
        elif not v and deb is not None:
            out.append((deb, y))
            deb = None
    if deb is not None:
        out.append((deb, len(lignes)))
    # on recolle les eclats (accents, jambages) : seul un fragment tres court
    # peut etre recolle, sinon deux lignes voisines fusionneraient
    fusion = []
    for a1, b1 in out:
        if fusion:
            precedent = fusion[-1]
            court = (b1 - a1) <= 6 or (precedent[1] - precedent[0]) <= 6
            if court and a1 - precedent[1] <= 3:
                fusion[-1] = (precedent[0], b1)
                continue
        fusion.append((a1, b1))
    res = []
    arr = np.array(im, dtype=np.int16)
    for a1, b1 in fusion:
        if b1 - a1 < 8:
            continue
        bande = arr[a1:b1, x0:x1]
        sombre = (bande.sum(axis=2) < 500)
        cols = np.where(sombre.any(axis=0))[0]
        if len(cols) == 0:
            continue
        res.append({"y0": a1, "y1": b1,
                    "x0": int(cols[0]) + x0, "x1": int(cols[-1]) + x0})
    return res


def couleurs(im, b):
    """pixels verts (pseudo), rouges (titre) et bleus (lien) d'une bande"""
    a = np.array(im.crop((b["x0"], b["y0"], b["x1"] + 1, b["y1"])), dtype=np.int16)
    r, g, bl = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    vert = int(((g > 90) & (g < 190) & (r < 90) & (bl < 90)).sum())
    rouge = int(((r > 150) & (g < 90) & (bl < 90)).sum())
    bleu = int(((bl > 130) & (r < 90) & (g < 90)).sum())
    # une vignette : beaucoup de pixels ni gris ni noirs
    ecart = np.abs(a - a.mean(axis=2, keepdims=True)).max(axis=2)
    couleur = int((ecart > 25).sum())
    return vert, rouge, bleu, couleur


def classe(im, b):
    v, r, bl, coul = couleurs(im, b)
    if v > 40:
        return "entete"
    if r > 40:
        return "titre"
    if bl > 40:
        return "lien"
    if b["y1"] - b["y0"] > 50 or coul > 3000:
        return "image"
    return "corps"


def analyse(chemin, zone=(30, 1265)):
    im = charge(chemin)
    out = []
    for b in bandes(im, x0=zone[0], x1=zone[1]):
        b["genre"] = classe(im, b)
        out.append(b)
    return im, out


BORD_DROIT = 1262      # bord interieur du cadre orange


def efface(d, b, gauche=None, marge=3, bord=None):
    x0 = b["x0"] if gauche is None else gauche
    d.rectangle([x0 - marge, b["y0"] - 4,
                 min(b["x1"] + marge + 80, bord or BORD_DROIT), b["y1"] + 3],
                fill=FOND)


CJK = "C:/Windows/Fonts/msgothic.ttc"      # pour les kaomoji


def ecrit(d, x, base_y, segments, taille=TAILLE):
    """segments : (texte, couleur) ou (texte, couleur, police)"""
    for seg in segments:
        texte, couleur = seg[0], seg[1]
        chemin = seg[2] if len(seg) > 2 else POLICE
        f = ImageFont.truetype(chemin, taille)
        d.text((x, base_y), texte, font=f, fill=couleur, anchor="ls")
        x += d.textlength(texte, font=f)
    return x
