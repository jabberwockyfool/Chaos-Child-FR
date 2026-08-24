# -*- coding: utf-8 -*-
"""Reecrit en francais le titre et le corps d'une page @chan de CHAOS;CHILD.

On ne recree pas la page : pour chaque ligne reperee, on efface l'encre et on
redessine le texte francais a la meme place (meme x de depart, meme ligne de
base). Les en-tetes, les vignettes, le cadre et les boutons ne sont pas touches.
"""
import importlib, io, sys
from PIL import Image, ImageDraw, ImageFont

import page

LARGEUR_MAX = 1250          # bord interieur du cadre


def segments(ligne):
    """normalise une ligne en liste de segments (texte, couleur[, police])"""
    if isinstance(ligne, str):
        return [(ligne, page.ENCRE)]
    return list(ligne)


def largeur(ligne, taille):
    im = Image.new("L", (4000, taille * 3), 255)
    d = ImageDraw.Draw(im)
    x = 20
    for seg in segments(ligne):
        chemin = seg[2] if len(seg) > 2 else page.POLICE
        f = ImageFont.truetype(chemin, taille)
        d.text((x, taille * 2), seg[0], font=f, fill=0, anchor="ls")
        x += d.textlength(seg[0], font=f)
    bb = im.point(lambda p: 255 - p).getbbox()
    return (bb[2] - bb[0]) if bb else 0


def ecrit_page(chemin, module, apercu=None):
    fil = importlib.import_module(module)
    zone = getattr(fil, "ZONE", (30, 1265))
    bord = getattr(fil, "BORD", page.BORD_DROIT)
    im, bandes = page.analyse(chemin, zone)
    # tout ce qui precede le premier en-tete (icones, boutons « becheck ») n'est pas du texte
    premiers = [i for i, b in enumerate(bandes) if b["genre"] == "entete"]
    debut = premiers[0] if premiers else 0
    # zones a ne pas toucher (art ASCII, blocs graphiques) declarees par le fil
    sauter = getattr(fil, "SAUTER", [])
    def ignoree(b):
        return any(a <= b["y0"] < z for a, z in sauter)
    corps = [b for b in bandes[debut:]
             if b["genre"] == "corps" and b["x0"] > zone[0] + 30 and not ignoree(b)]
    titres = [b for b in bandes
              if b["genre"] == "titre" and b["x1"] - b["x0"] < (zone[1] - zone[0]) - 40]

    if len(corps) != len(fil.CORPS):
        raise SystemExit("%d lignes de corps dans l'image, %d dans le fil"
                         % (len(corps), len(fil.CORPS)))

    d = ImageDraw.Draw(im)

    # --- titre pose a la main (titre sur deux lignes, boutons a cote) ---
    bloc = getattr(fil, "TITRE_BLOC", None)
    if bloc:
        d.rectangle(bloc["zone"], fill=page.FOND)
        for ligne in bloc["lignes"]:
            x, base_y, segs = ligne[0], ligne[1], ligne[2]
            taille = ligne[3] if len(ligne) > 3 else bloc.get("taille", page.TAILLE + 2)
            page.ecrit(d, x, base_y, segs, taille)

    # --- titre ---
    if not bloc and getattr(fil, "TITRE", None) and titres:
        b = titres[0]
        page.efface(d, b, gauche=b["x0"], marge=4, bord=bord)
        taille = page.TAILLE + 2
        while largeur(fil.TITRE, taille) > bord - 12 - b["x0"] and taille > 12:
            taille -= 1
        page.ecrit(d, b["x0"], b["y0"] + 17, fil.TITRE, taille)

    # --- corps ---
    trop_long = []
    for b, contenu in zip(corps, fil.CORPS):
        # un tuple = une bande qui porte deux lignes collees (jambages, kaomoji)
        lignes = list(contenu) if isinstance(contenu, tuple) else [contenu]
        page.efface(d, b, bord=bord)
        for k, ligne in enumerate(lignes):
            taille = page.TAILLE
            while b["x0"] + largeur(ligne, taille) > bord - 12 and taille > 12:
                taille -= 1
            if taille != page.TAILLE:
                trop_long.append((str(ligne)[:40], taille))
            page.ecrit(d, b["x0"], b["y0"] + 14 + 23 * k, segments(ligne), taille)

    im.save(chemin, optimize=True, compress_level=9)
    print("%s : %d lignes de corps%s reecrites"
          % (chemin.split("/")[-1], len(corps), " + titre" if (bloc or getattr(fil, "TITRE", None)) else ""))
    for t, s in trop_long:
        print("  reduit a %d : %s..." % (s, t))
    if apercu:
        im.resize((int(im.width * 0.78), int(im.height * 0.78))).save(apercu)


if __name__ == "__main__":
    ecrit_page(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
