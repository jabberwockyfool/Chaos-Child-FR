# -*- coding: utf-8 -*-
"""help00_steam, help01 : les ecrans d'aide (clavier et souris, manette).

Les etiquettes sont en Garamond gras, encre noire sur un vieux papier, chacune
reliee a sa touche par un trait de rappel. On les gomme par diffusion du
papier et on pose le francais aligne comme l'anglais sur son trait : a gauche
quand le trait arrive par la gauche ('g'), a droite quand il part a droite
('d'), centre quand il monte par-dessous ('c'). La largeur maximale, quand
elle est donnee, evite un trait ou une etiquette voisine.

Les noms des touches (ESC, CTRL, ENTER...) restent : ce sont ceux imprimes
sur un clavier.
"""
import numpy as np
from PIL import Image, ImageFilter

import habillage
import rebouche

GARAMOND_GRAS = "C:/Windows/Fonts/GARABD.TTF"
GARAMOND = "C:/Windows/Fonts/GARA.TTF"


def boite(a, fen):
    """L'encre de l'etiquette dans sa fenetre."""
    y0, y1, x0, x1 = fen
    z = a[y0:y1, x0:x1, :3].mean(axis=2)
    ys, xs = np.nonzero(z < 110)
    return (y0 + ys.min(), y0 + ys.max(), x0 + xs.min(), x0 + xs.max())


def etiquette(a, fen, aligne, en, fr, largeur_max=None, police=GARAMOND_GRAS,
              mesure=False):
    b = boite(a, fen)
    if mesure:
        print("   %-26s boite y %4d-%4d x %4d-%4d" % (en, b[0], b[1], b[2], b[3]))
        return
    y0, y1, x0, x1 = b
    z = a[y0 - 3:y1 + 4, x0 - 3:x1 + 4]
    lum = z[..., :3].mean(axis=2)
    encre = lum < 160
    # seulement l'encre de la boite : les traits de rappel s'arretent juste
    # a cote
    encre[:3] = encre[-3:] = False
    encre[:, :3] = encre[:, -3:] = False
    couleur = np.median(z[encre & (lum <= np.percentile(lum[encre], 15))][:, :3], axis=0)
    z[..., :3] = rebouche.diffuse(z[..., :3], rebouche.dilate(encre, 1), 300)
    g, y, _ = habillage.comme(en, fr, police, b, largeur_max=largeur_max)
    h, w = g.shape
    if aligne == "g":
        x = x0
    elif aligne == "d":
        x = x1 + 1 - w
    else:
        x = int(round((x0 + x1) / 2.0 - w / 2.0))
    bb = a[y:y + h, x:x + w, :3]
    bb[:] = bb * (1 - g[..., None]) + couleur * g[..., None]
    print("   %-26s -> %-32s %3d px (anglais %3d)" % (en, fr, w, x1 - x0 + 1))


def logo(a, lignes, zone):
    """Le tampon rouge (HELP / OPERATING INSTRUCTIONS) : Haettenschweiler
    blanc avec une ombre portee rouge sombre. On gomme lettres et ombre au
    rouge du tampon (avec son grain), puis on pose le francais, cale a gauche
    comme l'anglais, avec la meme ombre."""
    Y0, Y1, X0, X1 = zone
    z = a[Y0:Y1, X0:X1]
    rvb = z[..., :3]
    blanc = rvb.min(axis=2) > 235
    rouge = (rvb[..., 0] > 180) & (rvb[..., 1] < 120)
    base = np.median(rvb[rouge], axis=0)
    # les lignes de texte : bandes de rangees qui contiennent du blanc
    rangs = np.nonzero(blanc.sum(axis=1) > 3)[0]
    bandes, d = [], rangs[0]
    for k in range(1, len(rangs)):
        if rangs[k] > rangs[k - 1] + 2:
            bandes.append((d, rangs[k - 1]))
            d = rangs[k]
    bandes.append((d, rangs[-1]))
    boites = []
    for b0, b1 in bandes:
        xs = np.nonzero(blanc[b0:b1 + 1].any(axis=0))[0]
        boites.append((Y0 + b0, Y0 + b1, X0 + xs.min(), X0 + xs.max()))
    # gommage : les lettres et leur ombre (8 px)
    efface = rebouche.dilate(blanc, 8)
    grain = np.random.RandomState(3).normal(0, 1, rvb.shape) * np.array([4.0, 3, 2])
    rvb[efface] = base + grain[efface]
    for (en, fr, largeur), b in zip(lignes, boites):
        g, y, x = habillage.comme(en, fr, habillage.HATTEN, b, largeur_max=largeur)
        h, w = g.shape
        M = 8
        G = np.zeros((h + 2 * M, w + 2 * M))
        G[M:M + h, M:M + w] = g
        om = np.asarray(Image.fromarray((G * 255).astype("uint8"))
                        .transform((w + 2 * M, h + 2 * M), Image.AFFINE, (1, 0, -2, 0, 1, -3))
                        .filter(ImageFilter.GaussianBlur(2.5)), dtype=float) / 255.0
        bb = a[y - M:y + h + M, x - M:x + w + M, :3]
        bb[:] = bb * (1 - 0.4 * om[..., None])
        bb[:] = bb * (1 - G[..., None]) + 255.0 * G[..., None]
        print("   %-22s -> %-14s %3d px (anglais %3d)" % (en, fr, w, b[3] - b[2] + 1))


# (fenetre approximative (y0, y1, x0, x1), alignement, anglais, francais
#  [, largeur max])
CLAVIER = [
    ((232, 258, 650, 800), "d", "QUICK SAVE", "SAUVEGARDE RAPIDE"),
    ((232, 258, 905, 1010), "g", "CONFIG", "OPTIONS"),
    ((268, 294, 345, 470), "g", "BACKLOG", "HISTORIQUE"),
    # HISTORIQUE finit vers 505 sur la meme ligne
    ((270, 296, 575, 735), "d", "QUICK LOAD", "CHARGEMENT RAPIDE", 726 - 516),
    ((262, 288, 968, 1120), "g", "TITLE MENU", u"\u00c9CRAN TITRE"),
    ((313, 339, 312, 385), "g", "HELP", "AIDE"),
    ((313, 339, 414, 570), "g", "AUTO MODE", "MODE AUTO"),
    ((308, 334, 604, 672), "d", "SAVE", "SAUVER"),
    ((292, 318, 1036, 1302), "g", "TOGGLE FULLSCREEN", u"PLEIN \u00c9CRAN"),
    ((338, 364, 551, 628), "d", "LOAD", "CHARGER"),
    ((323, 349, 1104, 1272), "g", "SCREENSHOT", u"CAPTURE D\u2019\u00c9CRAN"),
    # le trait de F1 monte en x 350
    ((357, 383, 192, 330), "g", "END GAME", "QUITTER LE JEU", 143),
    ((354, 380, 1166, 1290), "c", "BACKLOG", "HISTORIQUE"),
    ((384, 410, 1286, 1442), "g", "AUTO MODE", "MODE AUTO"),
    ((382, 408, 1540, 1626), "g", "ENTER", "VALIDER"),
    ((440, 468, 1330, 1506), "g", "CANCEL, BACK", "ANNULER, RETOUR", 186),
    ((468, 494, 1326, 1506), "g", "HIDE TEXT", "MASQUER LE TEXTE", 186),
    ((433, 459, 1531, 1790), "g", "SCROLL TEXT & LISTS", u"D\u00c9FILER TEXTE ET LISTES", 330),
    ((460, 482, 1531, 1790), "g", "BACKLOG", "HISTORIQUE"),
    ((528, 554, 78, 257), "d", "SYSTEM MENU", u"MENU SYST\u00c8ME"),
    ((595, 621, 1314, 1404), "g", "ENTER", "VALIDER"),
    ((689, 714, 1483, 1660), "g", "CANCEL, BACK", "ANNULER, RETOUR"),
    ((714, 742, 1483, 1844), "g", "SYSTEM MENU (INGAME ONLY)", u"MENU SYST\u00c8ME (EN JEU)"),
    # entre le trait de CTRL (x 342) et celui de E (x 676)
    ((862, 888, 401, 644), "c", "DELUSION TRIGGER", u"D\u00c9CLENCHEUR DE D\u00c9LUSION", 284),
    ((860, 886, 784, 1126), "c", "SCROLL TEXT (IN TIPS MENU)", u"D\u00c9FILER LE TEXTE (DANS LES TIPS)", 330),
    ((899, 922, 1158, 1258), "c", "SELECT", "CHOISIR"),
    ((911, 937, 268, 413), "c", "FORCE SKIP", u"AVANCE FORC\u00c9E"),
    ((911, 937, 604, 743), "c", "SKIP MODE", "AVANCE RAPIDE"),
]

LOGO = ([("HELP", "AIDE", 330), ("OPERATING INSTRUCTIONS", u"MODE D\u2019EMPLOI", 330)],
        (55, 300, 1470, 1850))


def clavier(a, mesure=False):
    if not mesure:
        logo(a, *LOGO)
        # a l'interieur du double filet du cadre
        etiquette(a, (116, 162, 131, 650), "c", "KEYBOARD & MOUSE", "CLAVIER ET SOURIS",
                  510, police=GARAMOND)
    for e in CLAVIER:
        fen, al, en, fr = e[:4]
        etiquette(a, fen, al, en, fr, e[4] if len(e) > 4 else None, mesure=mesure)
    return a


if __name__ == "__main__":
    import ecrans
    import dds
    t = dds.lit(ecrans.reference("help00_steam.dds"))
    clavier(t["rgba"].astype(float), mesure=True)


# ------------------------------------------------------------------ manette

PERPETUA_TITRES = "C:/Windows/Fonts/PERTIBD.TTF"

MANETTE = [
    (u"Select", u"Choisir"),
    (u"Skip mode / Turn page (Right)", u"Avance rapide / Page suivante"),
    (u"Auto mode", u"Mode auto"),
    (u"Enter / Send message", u"Valider / Envoyer un message"),
    (u"Cancel / Hide text", u"Annuler / Masquer le texte"),
    (u"System menu", u"Menu syst\u00e8me"),
    (u"Delusion trigger (Left)", u"D\u00e9clencheur de d\u00e9lusion (gauche)"),
    (u"Delusion trigger (Right)", u"D\u00e9clencheur de d\u00e9lusion (droite)"),
    (u"TIPS", None),
    (u"Force skip / Turn page (Left)", u"Avance forc\u00e9e / Page pr\u00e9c\u00e9dente"),
    (u"Backlog", u"Historique"),
    (u"Quick save", u"Sauvegarde rapide"),
]
LIGNE_0, PAS = 278, 52.25        # centre de la premiere ligne, interligne


def entete(a, mots):
    """FUNCTION / KEY : lettres ajourees au pochoir dans la barre orange (on
    y voit le papier). On rebouche les lettres a l'orange de la barre, puis
    on decoupe le francais, rempli du papier pris dans une zone vierge."""
    Y0, Y1 = 200, 250
    for (x0, x1, dx), en, fr, largeur, centre in mots:
        z = a[Y0:Y1, x0:x1, :3]
        orange = (z[..., 0] - z[..., 2]) > 70
        barre = rebouche.dilate(orange, 3) & ~rebouche.dilate(~orange, 0)
        ys = np.nonzero(orange.mean(axis=1) > 0.3)[0]
        b0, b1 = ys.min(), ys.max()
        lettres = ~orange
        lettres[:b0] = lettres[b1 + 1:] = False
        z[:] = rebouche.diffuse(z, rebouche.dilate(lettres, 1) & (np.arange(z.shape[0])[:, None] >= b0)
                                & (np.arange(z.shape[0])[:, None] <= b1), 300)
        xs = np.nonzero(lettres.any(axis=0))[0]
        boite_en = (Y0 + b0, Y0 + b1, x0 + xs.min(), x0 + xs.max())
        g, y, x = habillage.comme(en, fr, PERPETUA_TITRES, boite_en, largeur_max=largeur)
        h, w = g.shape
        if centre:
            x = int(round((x0 + x1) / 2.0 - w / 2.0))
        papier = a[y:y + h, x + dx:x + dx + w, :3]
        bb = a[y:y + h, x:x + w, :3]
        bb[:] = bb * (1 - g[..., None]) + papier * g[..., None]
        print("   %-8s -> %-8s %3d px (anglais %3d)" % (en, fr, w, boite_en[3] - boite_en[2] + 1))


def manette(a, mesure=False):
    if not mesure:
        logo(a, *LOGO)
        etiquette(a, (117, 161, 129, 452), "c", "CONTROLLER", "MANETTE", 320, police=GARAMOND)
        entete(a, [((172, 762, 830), "FUNCTION", "FONCTION", 560, False),
                   ((772, 988, 230), "KEY", "TOUCHE", 196, True)])
        etiquette(a, (262, 296, 782, 980), "c", "D-pad / Joystick", "Croix / Joystick", 196,
                  police=GARAMOND)
    rangees(a, mesure)
    return a


def rangees(a, mesure=False):
    """Le tableau : un seul corps et une seule chasse pour toutes les lignes,
    cales sur "Auto mode" (sans jambage), chaque ligne posee sur sa ligne de
    base, a gauche de la case."""
    import habillage as hb
    from PIL import Image as Im
    ge, te, le, base = hb._rendu("Auto mode", GARAMOND_GRAS)
    ys, xs = np.nonzero(ge > 0.5)
    k = (393 - 368 + 1) / float(ys.max() - ys.min() + 1)
    c = (340 - 189 + 1) / float((xs.max() - xs.min() + 1) * k)
    base_ref = 393                                  # ligne 3, "Auto mode"
    for i, (en, fr) in enumerate(MANETTE):
        yc = int(round(LIGNE_0 + i * PAS))
        if mesure or fr is None:
            continue
        # gommage de toute l'encre de la case (les filets restent dehors)
        z = a[yc - 20:yc + 21, 182:756]
        lum = z[..., :3].mean(axis=2)
        encre = lum < 165
        couleur = np.median(z[encre & (lum <= np.percentile(lum[encre], 15))][:, :3], axis=0)
        z[..., :3] = rebouche.diffuse(z[..., :3], rebouche.dilate(encre, 1), 300)
        g, tf, lf, bf = hb._rendu(fr, GARAMOND_GRAS)
        cc = c
        if g.shape[1] * k * cc > 560:
            cc = 560 / float(g.shape[1] * k)
        W = int(round(g.shape[1] * k * cc))
        H = int(round(g.shape[0] * k))
        g = np.asarray(Im.fromarray((g * 255).astype("uint8")).resize((W, H), Im.LANCZOS),
                       dtype=float) / 255.0
        yb = base_ref + (i - 2) * PAS
        y = int(round(yb - (bf - tf) * k))
        x = 190
        bb = a[y:y + H, x:x + W, :3]
        bb[:] = bb * (1 - g[..., None]) + couleur * g[..., None]
        print("   %-30s -> %-34s %3d px%s" % (en, fr, W, " (resserre)" if cc < c else ""))
