# -*- coding: utf-8 -*-
"""config : l'ecran des options.

Presque tout y est en sprites "alpha" : le texte est dans le canal alpha, sur
transparent, avec une couleur unie (rouge pour les reglages, blanc ou noir
ailleurs). On gomme en vidant l'alpha et on pose le francais dans l'alpha.

- les reglages (Baskerville) sont suivis d'une ligne pointillee jusqu'a une
  colonne fixe, et parfois des boutons (L) (R) : la ligne est recomposee
  (texte, boutons deplaces, pointilles prolonges ou raccourcis) ;
- les rubriques (Haettenschweiler a gauche, icone et mot en Bodoni gras a
  droite) : le mot reste cale a droite, l'icone suit ;
- les valeurs (ON, OFF, FULL...), les noms "OTHERS", les vignettes, le logo
  et les bandeaux.

Les noms des personnages restent (ordre japonais, comme dans les scripts).
"""
import numpy as np

import habillage
import rebouche

HATTEN = habillage.HATTEN
BASKERVILLE = "C:/Windows/Fonts/BASKVILL.TTF"
BODONI = "C:/Windows/Fonts/BOD_B.TTF"


def _encre(a, fen, seuil=128):
    y0, y1, x0, x1 = fen
    ys, xs = np.nonzero(a[y0:y1, x0:x1, 3] > seuil)
    return (y0 + ys.min(), y0 + ys.max(), x0 + xs.min(), x0 + xs.max())


def _couleur(a, fen):
    y0, y1, x0, x1 = fen
    z = a[y0:y1, x0:x1]
    return np.median(z[z[..., 3] > 200][:, :3], axis=0)


def _pose(a, g, y, x, couleur):
    h, w = g.shape
    b = a[y:y + h, x:x + w]
    b[..., 3] = np.maximum(b[..., 3], 255.0 * g)
    b[g > 0.02, :3] = couleur


def libelle(a, fen, en, fr, police, aligne="g", largeur_max=None, plafond=None):
    """Un libelle alpha seul dans sa fenetre."""
    boite = _encre(a, fen)
    couleur = _couleur(a, fen)
    y0, y1, x0, x1 = fen
    a[y0:y1, x0:x1, 3] = 0
    g, y, _ = habillage.comme(en, fr, police, boite, largeur_max=largeur_max,
                              plafond=plafond)
    h, w = g.shape
    if aligne == "g":
        x = boite[2]
    elif aligne == "d":
        x = boite[3] + 1 - w
    else:
        x = int(round((boite[2] + boite[3]) / 2.0 - w / 2.0))
    _pose(a, g, y, x, couleur)
    print("   %-36s -> %-40s %3d px (anglais %3d)" % (en, fr, w, boite[3] - boite[2] + 1))
    return x, x + w - 1


# ---------------------------------------------------------------- reglages

X_REGLAGES = 1236
REGLAGES = [
    (1250, 1276, "MESSAGE SPEED", "VITESSE DU TEXTE"),
    (1302, 1329, "WAITING TIME FOR AUTO MODE", "ATTENTE DU MODE AUTO"),
    (1354, 1380, "SKIP MODE", "AVANCE RAPIDE"),
    (1406, 1433, "DISPLAY NOTIFICATIONS FOR NEW TIPS", "SIGNALER LES NOUVEAUX TIPS"),
    (1450, 1493, "SEND MESSAGES WITH", "ENVOYER LES MESSAGES AVEC"),
    (1502, 1545, "TRIGGER DELUSIONS WITH", u"D\u00c9CLENCHER LES D\u00c9LUSIONS AVEC"),
    (1560, 1587, "VOICE VOLUME", "VOLUME DES VOIX"),
    (1614, 1641, "BGM VOLUME", "VOLUME DE LA MUSIQUE"),
    (1666, 1693, "SOUND EFFECTS VOLUME", "VOLUME DES BRUITAGES"),
    (1718, 1745, "MOVIE VOLUME", u"VOLUME DES VID\u00c9OS"),
    (1770, 1797, "SYNCHRONIZE TEXT SPEED TO VOICES", "CALER LE TEXTE SUR LES VOIX"),
    (1822, 1849, "CANCEL VOICE PLAYBACK AT NEXT LINE", u"COUPER LA VOIX \u00c0 LA LIGNE SUIVANTE"),
    (1978, 2005, "STOP SKIP MODE AT DELUSION TRIGGERS", u"STOPPER L\u2019AVANCE AUX D\u00c9LUSIONS"),
    (2029, 2056, "FULLSCREEN MODE", u"MODE PLEIN \u00c9CRAN"),
    (2082, 2109, "SCREEN RESOLUTION", u"R\u00c9SOLUTION"),
]


def _segments(m, gap):
    c = m.any(axis=0)
    segs, i = [], 0
    while i < len(c):
        if c[i]:
            j = i
            while j < len(c) and c[j]:
                j += 1
            segs.append([i, j - 1])
            i = j
        else:
            i += 1
    out = []
    for s in segs:
        if out and s[0] - out[-1][1] <= gap:
            out[-1][1] = s[1]
        else:
            out.append(s)
    return out


def _periode(profil):
    """La periode des pointilles, par autocorrelation."""
    p = profil - profil.mean()
    best, per = None, 6
    for k in range(3, 20):
        c = (p[:-k] * p[k:]).sum()
        if best is None or c > best:
            best, per = c, k
    return per


def reglage(a, y0, y1, en, fr):
    Y0, Y1 = y0 - 3, y1 + 4
    z = a[Y0:Y1, X_REGLAGES:]
    al = z[..., 3] > 60
    # les boutons (L) (R) sont plus hauts que les lettres
    cap = al[(y1 - y0) // 2 - 9 + 3:(y1 - y0) // 2 + 9 + 3]
    segs = _segments(al, 14)
    pointilles = segs[-1]
    texte = segs[0]
    boutons = None
    haut = al.any(axis=1)
    if (y1 - y0) > 35:
        # ligne a boutons : le texte s'arrete ou la hauteur saute
        # ligne a boutons : les morceaux (ecart d'au moins 2 px) ; le premier
        # qui contient une colonne haute est le premier bouton
        morceaux = _segments(al[:, texte[0]:texte[1] + 1], 1)
        for k, (m0, m1) in enumerate(morceaux):
            col = al[:, texte[0] + m0:texte[0] + m1 + 1].any(axis=1)
            ys = np.nonzero(col)[0]
            if ys.max() - ys.min() > 32:
                break
        boutons = (texte[0] + m0, texte[1])
        texte = [texte[0], texte[0] + morceaux[k - 1][1]]
    d0, d1 = pointilles
    # le motif des pointilles, et sa rangee
    bande = z[:, d0:d1 + 1].copy()
    per = _periode(bande[..., 3].sum(axis=0))
    blocb = z[:, boutons[0]:boutons[1] + 1].copy() if boutons else None
    ecart_b = (boutons[0] - texte[1]) if boutons else 0
    ecart_p = d0 - ((boutons[1]) if boutons else texte[1])
    couleur = _couleur(a, (Y0, Y1, X_REGLAGES, X_REGLAGES + texte[1] + 1))
    # les capitales, sans les boutons
    lettres = (Y0 + np.nonzero(al[:, texte[0]:texte[1] + 1].any(axis=1))[0].min(),
               Y0 + np.nonzero(al[:, texte[0]:texte[1] + 1].any(axis=1))[0].max(),
               X_REGLAGES + texte[0], X_REGLAGES + texte[1])

    z[..., 3] = 0
    place = d1 - 60 - texte[0] - ((boutons[1] - boutons[0] + ecart_b) if boutons else 0)
    g, y, _ = habillage.comme(en, fr, BASKERVILLE, lettres, largeur_max=place)
    h, w = g.shape
    x = lettres[2]
    _pose(a, g, y, x, couleur)
    fin = x + w - 1 - X_REGLAGES
    if boutons:
        nb0 = fin + ecart_b
        z[:, nb0:nb0 + blocb.shape[1]] = blocb
        fin = nb0 + blocb.shape[1] - 1
    n0 = fin + ecart_p
    for xx in range(n0, d1 + 1):
        src = xx if xx >= d0 else xx + ((d0 - xx + per - 1) // per) * per
        if src > d1:
            continue
        z[:, xx] = bande[:, src - d0]
    print("   %-36s -> %-40s %3d px (anglais %3d)%s"
          % (en, fr, w, texte[1] - texte[0] + 1, ", boutons deplaces" if boutons else ""))


# ---------------------------------------------------------------- rubriques

RUBRIQUES = [
    # (rangee, gauche : anglais, francais ; droite : icone (x0, x1), mot)
    ((1518, 1572), "BASIC SETTINGS", u"PARAM\u00c8TRES G\u00c9N\u00c9RAUX", (739, 773), "BASIC", u"G\u00c9N\u00c9RAL"),
    ((1603, 1652), "TEXT SETTINGS", u"PARAM\u00c8TRES DU TEXTE", (722, 778), "TEXT", "TEXTE"),
    ((1677, 1732), "SOUND SETTINGS", u"PARAM\u00c8TRES DU SON", (729, 758), "SOUND", "SON"),
    ((1763, 1812), "CHARACTER VOICE SETTINGS", "VOIX DES PERSONNAGES", (719, 777), "VOICE", "VOIX"),
]


def rubrique(a, rang, en_g, fr_g, icone, en_d, fr_d):
    Y0, Y1 = rang
    # a gauche
    libelle(a, (Y0 + 16, Y1, 0, 420), en_g, fr_g, HATTEN, "g")
    # a droite : le mot, cale a droite ; l'icone le suit
    i0, i1 = icone
    mot = _encre(a, (Y0, Y1, i1 + 3, 946))
    couleur = _couleur(a, (Y0, Y1, i1 + 3, 946))
    bloc = a[Y0:Y1, i0:i1 + 1].copy()
    ecart = mot[2] - i1
    a[Y0:Y1, i0:946, 3] = 0
    g, y, _ = habillage.comme(en_d, fr_d, BODONI, mot, largeur_max=946 - 470)
    h, w = g.shape
    x = mot[3] + 1 - w
    _pose(a, g, y, x, couleur)
    n1 = x - ecart
    n0 = n1 - (i1 - i0)
    z = a[Y0:Y1, n0:n1 + 1]
    m = bloc[..., 3] > 0
    z[m] = bloc[m]
    print("   %-36s -> %-40s %3d px (anglais %3d), icone en %d"
          % (en_d, fr_d, w, mot[3] - mot[2] + 1, n0))


# ------------------------------------------------------------------ valeurs

VALEURS = [
    ((1400, 1440, 700, 958), "FULL", "PLEIN"),
    ((1452, 1492, 700, 958), "WINDOW", u"FEN\u00caTRE"),
    ((1400, 1440, 958, 1120), "READ-ONLY", u"D\u00c9J\u00c0 LU"),
    ((1452, 1492, 958, 1120), "ALL", "TOUT"),
    ((1504, 1544, 958, 1120), "ON", "OUI"),
    ((1556, 1596, 958, 1120), "OFF", "NON"),
    ((1609, 1649, 958, 1120), "ON", "OUI"),
    ((1661, 1701, 958, 1120), "OFF", "NON"),
]

NOMS = [
    ((1918, 1960, 655, 870), "OTHERS (MALE)", "AUTRES (HOMMES)", 870 - 661 - 8),
    ((1918, 1960, 872, 1090), "OTHERS (FEMALE)", "AUTRES (FEMMES)", 1090 - 878 - 8),
]

# les vignettes : (fenetre du mot, anglais, francais)
VIGNETTES = [
    ((228, 270, 1690, 1775), "BASIC", u"G\u00c9N\u00c9RAL"),
    ((452, 492, 1728, 1800), "TEXT", "TEXTE"),
    ((690, 732, 1698, 1792), "SOUND", "SON"),
    ((912, 955, 1718, 1800), "VOICE", "VOIX"),
    ((2328, 2374, 70, 155), "BASIC", u"G\u00c9N\u00c9RAL"),
    ((2326, 2366, 302, 372), "TEXT", "TEXTE"),
    ((2328, 2372, 513, 607), "SOUND", "SON"),
    ((2325, 2370, 743, 824), "VOICE", "VOIX"),
    ((2328, 2374, 967, 1051), "BASIC", u"G\u00c9N\u00c9RAL"),
    ((2326, 2366, 1198, 1269), "TEXT", "TEXTE"),
    ((2328, 2372, 1409, 1503), "SOUND", "SON"),
    ((2325, 2370, 1638, 1720), "VOICE", "VOIX"),
]

BANDEAUX = [
    ((2419, 2469), (2428, 2458), [
        ((110, 196, 234), "SELECT", "CHOISIR"),
        ((271, 386, 424), "CONFIRM", "VALIDER"),
        ((476, 574, 612), "DEFAULT", u"PAR D\u00c9FAUT"),
        ((664, 835, 872), "TOGGLE MUTE", "COUPER LE SON"),
        ((916, 980, 1300), "BACK", "RETOUR"),
    ]),
    ((2479, 2528), (2488, 2518), [
        ((110, 196, 234), "SELECT", "CHOISIR"),
        ((271, 386, 424), "CONFIRM", "VALIDER"),
        ((476, 574, 612), "DEFAULT", u"PAR D\u00c9FAUT"),
        ((656, 720, 1300), "BACK", "RETOUR"),
    ]),
]


def ecran(a):
    habillage.logo(a, (1240, 1512, 0, 680),
                   [(1240, 1512, "CONFIG", "OPTIONS")], 655)
    for y0, y1, en, fr in REGLAGES:
        reglage(a, y0, y1, en, fr)
    for r in RUBRIQUES:
        rubrique(a, *r)
    for fen, en, fr in VALEURS:
        libelle(a, fen, en, fr, HATTEN, "c")
    for fen, en, fr, lm in NOMS:
        libelle(a, fen, en, fr, HATTEN, "g", largeur_max=lm)
    for (y0, y1, x0, x1), en, fr in VIGNETTES:
        # la fenetre doit contenir le francais, plus long
        fen = (y0, y1, x0 - 30, x1 + 30)
        habillage.panneau(a, fen, en, fr, True, (15, 35), incliner=True,
                          large=70, rouille=False, seuil=215, marge=6)
    for lignes, cap, mots in BANDEAUX:
        habillage.bandeau(a, lignes, cap, mots)
    return a
