# -*- coding: utf-8 -*-
"""Refait les repliques de tchat en surimpression (calques CC_HANA_*).

Ces images sont transparentes partout sauf le texte : il n'y a pas de fond a
reconstituer, seulement a redessiner la ligne.

Structure de l'original, relevee au pixel : du Century Gothic resserre a 94 %
en largeur, blanc, pose sur un lisere noir adouci. La couche alpha vaut
max(lettre, lisere) et le RVB vaut 255 x lettre / alpha, c'est-a-dire du blanc
compose sur du noir.

Le reglage se lit sur l'original : le corps vient de la hauteur de la ligne
anglaise, l'espacement de sa largeur. Le francais est ensuite rendu avec ce
meme reglage, donc a la meme taille que l'anglais qu'il remplace.

    python cg/outils/surimpression.py --controle <ref.png> "<anglais>"
    python cg/outils/surimpression.py <ref.png> <sortie.png> "<anglais>" "<francais>"

Un segment entre crochets est colorie comme dans les variantes _B :
"[Ban] de compte !".
"""
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

POLICE = "C:/Windows/Fonts/GOTHIC.TTF"   # Century Gothic
ECHELLE = 0.94        # l'original est un peu plus etroit que la police nue
SUR = 4               # surechantillonnage du rendu
RAYON, FLOU, FORCE = 1, 0.85, 1.05        # le lisere noir, releve sur l'original
MARGE_ECRAN = 16


def _rendu(texte, taille, chasse, police=POLICE):
    ft = ImageFont.truetype(police, taille * SUR)
    large = int((taille * SUR) * (len(texte) + 2) * 1.6) + 400
    img = Image.new("L", (large, taille * SUR * 3), 0)
    d = ImageDraw.Draw(img)
    origine = taille * SUR
    x = float(origine)
    bornes = []
    for c in texte:
        d.text((x, taille * SUR // 2), c, 255, font=ft)
        w = d.textlength(c, font=ft)
        bornes.append((x, x + w))
        x += w + chasse * SUR
    return img, bornes


def lettre(texte, taille, chasse, segments=None, police=POLICE):
    """Couverture de la ligne, le masque du segment colorie, et la hauteur de
    l'encre au-dessus de l'origine du trace (pour caler sur la ligne de base)."""
    img, bornes = _rendu(texte, taille, chasse, police)
    a = np.asarray(img, dtype=float) / 255.0
    r = np.nonzero((a > 0.5).any(axis=1))[0]
    c = np.nonzero((a > 0.5).any(axis=0))[0]
    y0, x0 = r.min(), c.min()
    a = a[y0:r.max() + 1, x0:c.max() + 1]
    h, w = a.shape
    cible = (max(1, int(round(w * ECHELLE / SUR))), max(1, h // SUR))
    petit = np.asarray(Image.fromarray((a * 255).astype("uint8"))
                       .resize(cible, Image.LANCZOS), dtype=float) / 255.0
    dessus = (taille * SUR // 2) - y0      # encre au-dessus de l'origine
    if not segments:
        return petit, None, dessus / float(SUR)
    marque = np.zeros_like(a)
    for i, j in segments:
        g = int(bornes[i][0] - x0)
        dte = int(bornes[j - 1][1] - x0)
        marque[:, max(0, g - 2):dte + 2] = 1.0
    mp = np.asarray(Image.fromarray((marque * 255).astype("uint8"))
                    .resize(cible, Image.LANCZOS), dtype=float) / 255.0
    return petit, mp > 0.5, dessus / float(SUR)


def contour(m, lisere=None):
    """lisere = (rayon, flou, force) ; par defaut le reglage releve sur les
    repliques ordinaires."""
    rayon, flou, force = lisere if lisere else (RAYON, FLOU, FORCE)
    im = Image.fromarray((np.clip(m, 0, 1) * 255).astype("uint8"))
    for _ in range(rayon):
        im = im.filter(ImageFilter.MaxFilter(3))
    im = im.filter(ImageFilter.GaussianBlur(flou))
    return np.clip(np.asarray(im, dtype=float) / 255.0 * force, 0, 1)


def calque(m, taille_image, x, y, couleur=(255, 255, 255),
           marque=None, couleur_marque=None, lisere=None):
    marge = 6
    grand = np.zeros((m.shape[0] + 2 * marge, m.shape[1] + 2 * marge))
    grand[marge:marge + m.shape[0], marge:marge + m.shape[1]] = m
    gm = np.zeros(grand.shape, bool)
    if marque is not None:
        gm[marge:marge + m.shape[0], marge:marge + m.shape[1]] = marque
    o = contour(grand, lisere)
    alpha = np.maximum(grand, o)
    rgb = np.zeros(alpha.shape + (3,))
    sur = alpha > 0
    base = np.zeros(alpha.shape + (3,))
    base[:] = np.array(couleur, dtype=float)
    if marque is not None and couleur_marque is not None:
        base[gm] = np.array(couleur_marque, dtype=float)
    rgb[sur] = base[sur] * (grand[sur] / alpha[sur])[:, None]
    out = np.zeros((taille_image[1], taille_image[0], 4))
    h, w = alpha.shape
    y0, x0 = y - marge, x - marge
    y1, x1 = min(out.shape[0], y0 + h), min(out.shape[1], x0 + w)
    out[max(0, y0):y1, max(0, x0):x1, :3] = rgb[max(0, -y0):y1 - y0, max(0, -x0):x1 - x0]
    out[max(0, y0):y1, max(0, x0):x1, 3] = alpha[max(0, -y0):y1 - y0, max(0, -x0):x1 - x0] * 255
    return Image.fromarray(np.clip(out, 0, 255).astype("uint8"), "RGBA")


def mesure(chemin):
    a = np.asarray(Image.open(chemin).convert("RGBA"), dtype=float)
    plein = (a[..., 3] > 170) & (a[..., :3].max(axis=2) > 170)
    ys, xs = np.nonzero(plein)
    vif = (a[..., 3] > 240) & (a[..., :3].min(axis=2) > 150)
    coul = a[..., :3][vif]
    return dict(taille_image=(a.shape[1], a.shape[0]),
                haut=int(ys.min()), bas=int(ys.max()),
                gauche=int(xs.min()), droite=int(xs.max()),
                hauteur=int(ys.max() - ys.min() + 1),
                largeur=int(xs.max() - xs.min() + 1),
                couleur=tuple(int(v) for v in coul.mean(axis=0).round()) if len(coul) else (255, 255, 255))


def regle(anglais, hauteur, largeur, police=POLICE):
    """Corps d'apres la hauteur, espacement d'apres la largeur de l'anglais."""
    taille = 10
    for t in range(10, 90):
        if lettre(anglais, t, 0.0, None, police)[0].shape[0] >= hauteur:
            taille = t
            break
    lo, hi = -2.0, 16.0
    for _ in range(26):
        ch = (lo + hi) / 2
        if lettre(anglais, taille, ch, None, police)[0].shape[1] < largeur:
            lo = ch
        else:
            hi = ch
    return taille, ch


def decoupe(texte):
    """Retire les crochets et rend les bornes du segment colorie."""
    segs, net, i = [], [], 0
    for bout in re.split(r"(\[[^\]]*\])", texte):
        if bout.startswith("["):
            segs.append((i, i + len(bout) - 2))
            net.append(bout[1:-1])
            i += len(bout) - 2
        else:
            net.append(bout)
            i += len(bout)
    return "".join(net), segs


def compose(ref, anglais, francais, police=POLICE, lisere=None):
    m = mesure(ref)
    taille, ch = regle(anglais, m["hauteur"], m["largeur"], police)
    net, segs = decoupe(francais)
    g, marque, dessus = lettre(net, taille, ch, segs, police)
    # on cale sur la ligne de base, pas sur le haut : sinon un accent pousse
    # toute la ligne vers le bas
    _, _, dessus_en = lettre(anglais, taille, ch, None, police)
    y = m["haut"] - int(round(dessus - dessus_en))
    # on garde le bord gauche ; si la ligne deborde a droite, on la recale
    x = m["gauche"]
    if x + g.shape[1] > m["taille_image"][0] - MARGE_ECRAN:
        x = max(MARGE_ECRAN, m["droite"] + 1 - g.shape[1])
    if x + g.shape[1] > m["taille_image"][0] - MARGE_ECRAN:
        while ch > 0 and x + g.shape[1] > m["taille_image"][0] - MARGE_ECRAN:
            ch -= 0.25
            g, marque, dessus = lettre(net, taille, ch, segs, police)
        while x + g.shape[1] > m["taille_image"][0] - MARGE_ECRAN and taille > 10:
            taille -= 1
            g, marque, dessus = lettre(net, taille, ch, segs, police)
        x = max(MARGE_ECRAN, m["taille_image"][0] - MARGE_ECRAN - g.shape[1])
    im = calque(g, m["taille_image"], x, y, m["couleur"], marque, CYAN, lisere)
    return im, m, taille, ch, g.shape[1], x


CYAN = (130, 245, 255)


def main():
    controle = "--controle" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if controle:
        ref, anglais = args[0], args[1]
        im, m, taille, ch, larg, x = compose(ref, anglais, anglais)
        print("%s : hauteur %d, largeur %d -> corps %d, espacement %+.2f, rendu %d px"
              % (os.path.basename(ref), m["hauteur"], m["largeur"], taille, ch, larg))
        orig = Image.open(ref).convert("RGBA")
        b = (max(0, m["gauche"] - 12), max(0, m["haut"] - 12),
             min(m["taille_image"][0], max(m["droite"], x + larg) + 12),
             min(m["taille_image"][1], m["bas"] + 12))
        F = Image.new("RGB", (b[2] - b[0], 2 * (b[3] - b[1]) + 6), (235, 235, 238))
        for i, img in enumerate((orig, im)):
            c = img.crop(b)
            f = Image.new("RGB", c.size, (235, 235, 238))
            f.paste(c, mask=c.split()[3])
            F.paste(f, (0, i * (c.size[1] + 6)))
        F.resize((F.size[0] * 2, F.size[1] * 2), Image.LANCZOS).save("controle.png")
        print("controle.png ecrit (original au-dessus)")
        return
    ref, sortie, anglais, francais = args[0], args[1], args[2], args[3]
    im, m, taille, ch, larg, x = compose(ref, anglais, francais)
    im.save(sortie, optimize=True, compress_level=9)
    print("%-20s corps %d, espacement %+.2f, %d px (anglais %d) a x=%d"
          % (os.path.basename(sortie), taille, ch, larg, m["largeur"], x))


if __name__ == "__main__":
    main()
