# -*- coding: utf-8 -*-
"""menuchip : le menu systeme (12 entrees en deux etats) et ses bandeaux.

Chaque entree est un mot en Haettenschweiler sur une tache de bombe :
- etat repos (en haut) : tache blanche, les lettres ajourees dans l'alpha ;
  elles debordent de la tache, qui est a peu pres de la largeur du mot ;
- etat survol (en bas) : tache orange, lettres blanches.
Les taches ne sont pas les memes d'un etat a l'autre.

Le francais est souvent plus long : la tache est elargie horizontalement dans
le rapport des largeurs du mot (au plus ETIRE_MAX, et sans sortir de sa case,
le jeu decoupant le sprite dans la case) ; au-dela, le texte est resserre.
"""
import numpy as np
from PIL import Image, ImageFilter

import habillage
import localise
import rebouche

HATTEN = habillage.HATTEN
ETIRE_MAX = 2.0

COLONNES = [(2240, 2785), (2785, 3300), (3300, 3850)]
# (colonne, boite des capitales au survol (y0, y1, x0, x1), centre
#  approximatif du mot au repos (y, x), anglais, francais)
ENTREES = [
    (0, (1689, 1736, 2368, 2525), (168, 2447), "BACKLOG", "HISTORIQUE"),
    (0, (1924, 1971, 2359, 2559), (401, 2459), "QUICK SAVE", "SAUVEGARDE RAPIDE"),
    (0, (2203, 2250, 2357, 2558), (681, 2457), "QUICK LOAD", "CHARGEMENT RAPIDE"),
    (0, (2487, 2534, 2404, 2491), (964, 2447), "SAVE", "SAUVEGARDER"),
    (0, (2750, 2797, 2418, 2504), (1227, 2461), "LOAD", "CHARGER"),
    (1, (1635, 1682, 2874, 3042), (112, 2958), "TIPS LIST", "LISTE DES TIPS"),
    (1, (1911, 1958, 2891, 3015), (387, 2953), "CONFIG", "OPTIONS"),
    (1, (2215, 2262, 2874, 3096), (692, 2985), "FULL SCREEN", u"PLEIN ÉCRAN"),
    (1, (2492, 2538, 2899, 2980), (967, 2940), "HELP", "AIDE"),
    (1, (2758, 2804, 2887, 3119), (1234, 3003), "TITLE MENU", u"ÉCRAN TITRE"),
    (2, (1665, 1712, 3415, 3633), (142, 3524), "CLOSE MENU", "FERMER LE MENU"),
    (2, (1968, 2015, 3477, 3663), (444, 3570), "EXIT GAME", "QUITTER LE JEU"),
]

BANDEAUX = [
    ((1385, 1434), (1394, 1424), [
        ((110, 196, 234), "SELECT", "CHOISIR"),
        ((271, 386, 423), "CONFIRM", "VALIDER"),
        ((467, 531, 1100), "BACK", "RETOUR"),
    ]),
    ((1490, 1539), (1499, 1529), [((110, 173, 1100), "BACK", "RETOUR")]),
    ((1602, 1651), (1611, 1641), [
        ((110, 196, 234), "SELECT", "CHOISIR"),
        ((278, 341, 1100), "BACK", "RETOUR"),
    ]),
]


def _ferme(m, r):
    return ~rebouche.dilate(~rebouche.dilate(m, r), r)


def _gabarit(en, h, w):
    """L'anglais rendu dans la boite de ses capitales (h x w) ; la queue du Q
    depasse en dessous."""
    g, te, _, base = habillage._rendu(en, HATTEN)
    k = h / float(base - te)
    W = int(round(w))
    H = int(round(g.shape[0] * k))
    return np.asarray(Image.fromarray((g * 255).astype("uint8")).resize((W, H), Image.LANCZOS),
                      dtype=float) / 255.0


def _etire(z, cx, f):
    """Elargit z horizontalement d'un facteur f autour de la colonne cx."""
    w = z.shape[1]
    x = np.arange(w, dtype=float)
    src = np.clip(cx + (x - cx) / f, 0, w - 1.001)
    x0 = np.floor(src).astype(int)
    t = (src - x0)[None, :, None]
    return z[:, x0] * (1 - t) + z[:, x0 + 1] * t


def _tache(alpha, y0, y1, xm):
    """Etendue de la partie pleine de la tache sur la bande des lettres."""
    plein = (alpha[y0:y1 + 1] > 200).mean(axis=0) >= 0.5
    g = d = int(xm)
    while g > 0 and plein[g - 1]:
        g -= 1
    while d < len(plein) - 1 and plein[d + 1]:
        d += 1
    return g, d


def facteur(a, col, boite, en, fr):
    """L'elargissement que permet la tache dans sa case."""
    X0, X1 = COLONNES[col]
    y0, y1, x0, x1 = boite
    w_en = x1 - x0 + 1
    w_fr = habillage.comme(en, fr, HATTEN, boite)[0].shape[1]
    alpha = a[y0:y1 + 1, X0:X1, 3]
    xm = (x0 + x1) / 2.0 - X0
    plein = (alpha > 200).mean(axis=0) >= 0.5
    g = d = int(xm)
    while g > 0 and plein[g - 1]:
        g -= 1
    while d < len(plein) - 1 and plein[d + 1]:
        d += 1
    cx = (g + d) / 2.0
    demi = max(cx - g, d - cx, w_en / 2.0) + 40          # tache + halo
    f = min(ETIRE_MAX, max(1.0, w_fr / float(w_en)))
    return max(1.0, min(f, (min(cx, X1 - X0 - cx) - 2) / demi))


def puce(a, col, boite, en, fr, survol, f):
    X0, X1 = COLONNES[col]
    y0, y1, x0, x1 = boite
    Y0, Y1 = max(0, y0 - 110), y1 + 110
    z = a[Y0:Y1, X0:X1]
    ly0, ly1, lx0, lx1 = y0 - Y0, y1 - Y0, x0 - X0, x1 - X0
    alpha = z[..., 3]

    # gommage. Au survol, les lettres sont le blanc ; au repos, le gabarit
    # pose sur la boite, limite a la tache (les lettres en debordent)
    if survol:
        lettres = (alpha > 250) & (z[..., :3].min(axis=2) > 225)
        lettres[:max(0, ly0 - 10)] = False
        lettres[ly1 + 14:] = False
        trou = rebouche.dilate(lettres, 1)
        orange = np.median(z[(alpha > 250) & ~trou][:, :3], axis=0)
        z[trou, :3] = orange
    else:
        g = _gabarit(en, ly1 - ly0 + 1, lx1 - lx0 + 1)
        m = np.zeros(alpha.shape, bool)
        hh = min(g.shape[0], m.shape[0] - ly0)
        m[ly0:ly0 + hh, lx0:lx0 + g.shape[1]] = g[:hh] > 0.15
        tache = _ferme(alpha > 128, 14)
        z[rebouche.dilate(m, 2) & tache, 3] = 255.0

    # elargissement de la tache
    w_en = lx1 - lx0 + 1
    w_fr = habillage.comme(en, fr, HATTEN, boite)[0].shape[1]
    xm = (lx0 + lx1) / 2.0
    cg, cd = _tache(z[..., 3], ly0, ly1, xm)
    cx = (cg + cd) / 2.0
    if f > 1.02:
        z[:] = _etire(z.copy(), cx, f)
        if survol:
            z[z[..., 3] > 250, :3] = orange
        else:
            z[..., :3] = 255.0
    g, y, _ = habillage.comme(en, fr, HATTEN, boite, largeur_max=w_en * f)
    h, w = g.shape
    xc = X0 + cx + (xm - cx) * f              # le mot garde sa place
    x = int(round(xc - w / 2.0))
    # sous-couche : la tache doit couvrir le texte (au survol, tout le mot ;
    # au repos, ou les lettres debordent par dessein, les seuls accents)
    M = 8
    G = np.zeros((h + 2 * M, w + 2 * M))
    G[M:M + h, M:M + w] = g
    if not survol:
        G[M + (boite[0] - y):] = 0
    sous = np.asarray(Image.fromarray((G * 255).astype("uint8"))
                      .filter(ImageFilter.MaxFilter(11))
                      .filter(ImageFilter.GaussianBlur(1.5)), dtype=float) / 255.0
    sb = a[y - M:y + h + M, x - M:x + w + M]
    nouveau = sous * 255.0 > sb[..., 3]
    sb[..., 3] = np.maximum(sb[..., 3], sous * 255.0)
    sb[nouveau, :3] = orange if survol else 255.0
    bb = a[y:y + h, x:x + w]
    if survol:
        bb[..., :3] = bb[..., :3] * (1 - g[..., None]) + 255.0 * g[..., None]
    else:
        bb[..., 3] = bb[..., 3] * (1 - g)
    print("   %-11s -> %-18s %3d px (anglais %3d%s) %s"
          % (en, fr, w, w_en, ", tache x%.2f" % f if f > 1.02 else "",
             "survol" if survol else "repos"))


def boite_repos(a, yc, xc, en, h, w):
    """La boite du mot au repos : le gabarit cale sur les trous de la tache,
    autour de la position relevee."""
    g = (_gabarit(en, h, w)[:h] > 0.5).astype(float)
    y0, x0 = max(0, yc - h // 2 - 30), xc - w // 2 - 30
    z = a[y0:yc + h // 2 + 30, x0:xc + w // 2 + 30, 3]
    # +1 pour un trou dans la tache, -1 pour la tache pleine, 0 au-dehors
    # (au-dessus de la tache, tout est transparent : sans cela, le gabarit y
    # trouve un aussi bon score que sur les vraies lettres)
    tache = _ferme(z > 128, 14)
    poids = np.where(tache, np.where(z < 128, 1.0, -1.0), 0.0)
    sc = localise._correle(poids, g)
    y, x = divmod(int(np.argmax(sc)), sc.shape[1])
    return (y0 + y, y0 + y + h - 1, x0 + x, x0 + x + w - 1)


TIMES_GRAS = "C:/Windows/Fonts/timesbd.ttf"


def gravure(a):
    """PRESENT SITUATION, grave dans la gorge du bas du cadre. La moulure est
    la meme tout le long : on rebouche avec la gorge prise plus a gauche
    (fondue aux bords), puis on grave le francais, avec un lisere sombre en
    bas a droite comme l'original."""
    Y0, Y1, X0, X1 = 1258, 1283, 990, 1212
    L = X1 - X0
    src = a[Y0:Y1, X0 - L - 260:X1 - L - 260, :3].copy()
    z = a[Y0:Y1, X0:X1, :3]
    t = np.ones(L)
    F = 12
    t[:F] = np.linspace(0, 1, F + 2)[1:-1]
    t[-F:] = np.linspace(1, 0, F + 2)[1:-1]
    z[:] = z * (1 - t[None, :, None]) + src * t[None, :, None]
    couleur = np.array([181.0, 170, 123])
    g, y, x = habillage.comme("PRESENT SITUATION", "SITUATION ACTUELLE", TIMES_GRAS,
                              (1263, 1277, 1000, 1199), largeur_max=205)
    h, w = g.shape
    x = int(round((1000 + 1199) / 2.0 - w / 2.0))
    om = a[y + 1:y + h + 1, x + 1:x + w + 1, :3]
    om[:] = om * (1 - 0.6 * g[..., None]) + np.array([10.0, 25, 12]) * 0.6 * g[..., None]
    b = a[y:y + h, x:x + w, :3]
    b[:] = b * (1 - g[..., None]) + couleur * g[..., None]
    print("   PRESENT SITUATION -> SITUATION ACTUELLE %d px (anglais 200)" % w)


def menu(a):
    gravure(a)
    for col, b, (yc, xc), en, fr in ENTREES:
        h, w = b[1] - b[0] + 1, b[3] - b[2] + 1
        br = boite_repos(a, yc, xc, en, h, w)
        f = min(facteur(a, col, br, en, fr), facteur(a, col, b, en, fr))
        puce(a, col, br, en, fr, False, f)
        puce(a, col, b, en, fr, True, f)
    for lignes, cap, mots in BANDEAUX:
        habillage.bandeau(a, lignes, cap, mots)
    return a
