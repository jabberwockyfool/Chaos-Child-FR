# -*- coding: utf-8 -*-
"""Planche de contact lisible : n images par page, titrees."""
import sys
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS = None

DOSSIER = r"C:/Users/pc/AppData/Local/Temp/claude/d--cc-Lycoris-Lycoris/951ae2ff-abee-49e1-abc3-86a15eef0b46/scratchpad/cc/img/"


def planche(noms, sortie, cols=3, larg=620):
    vues = []
    for n in noms:
        im = Image.open(DOSSIER + n).convert("RGBA")
        fond = Image.new("RGB", im.size, (235, 235, 238))
        fond.paste(im, mask=im.split()[3])
        h = max(1, int(round(fond.size[1] * larg / float(fond.size[0]))))
        vues.append((n, fond.resize((larg, h), Image.LANCZOS)))
    hmax = max(v.size[1] for _, v in vues)
    lignes = (len(vues) + cols - 1) // cols
    F = Image.new("RGB", (cols * larg, lignes * (hmax + 16)), (16, 16, 18))
    d = ImageDraw.Draw(F)
    for i, (n, v) in enumerate(vues):
        x = (i % cols) * larg
        y = (i // cols) * (hmax + 16)
        d.text((x + 3, y + 2), n, fill=(255, 205, 60))
        F.paste(v, (x, y + 16))
    F.save(sortie)
    return F.size


if __name__ == "__main__":
    noms = sys.argv[2:]
    print(planche(noms, sys.argv[1]))
