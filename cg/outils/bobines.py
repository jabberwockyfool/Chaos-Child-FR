# -*- coding: utf-8 -*-
"""movmenu : les huit bobines de la galerie des videos.

Rangee du haut : quatre bobines ; rangee du bas (584 px plus bas, aligne sur
les blocs DXT) : les memes, une main rouge peinte par-dessus. On ne traite que
la rangee du haut, puis on reporte la difference (nouveau - ancien) sur celle
du bas, partout ou il n'y a pas de peinture : le leger bruit propre a chaque
rangee est garde, et la main reste par-dessus.

Sur chaque bobine, une etiquette de papier tournee porte les credits de la
chanson, en Garamond. Les titres et les noms restent ; les roles (Lyrics,
Composition, Arrangement, Sung by) sont traduits. Chaque role est donne par
le segment de sa ligne mediane (releve a la main sur un agrandissement) : on
retient les composantes d'encre proches du segment, on les gomme, et on pose
le francais avec la rotation et l'inclinaison de l'anglais.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import composantes
import habillage
import localise
import rebouche

GARAMOND = "C:/Windows/Fonts/GARA.TTF"
DECALE = 584                     # de la rangee du haut a celle du bas
NB = u"\u00a0"                   # espace insecable avant les deux-points

LYR_COMP = ("Lyrics/Composition:", u"Paroles/Composition" + NB + ":")
ARR = ("Arrangement:", u"Arrangement" + NB + ":")
SUNG = ("Sung by:", u"Chant" + NB + ":")
LYR = ("Lyrics:", u"Paroles" + NB + ":")
COMP = ("Composition:", u"Composition" + NB + ":")
COMP_ARR = ("Composition/Arrangement:", u"Composition/Arrangement" + NB + ":")

# (debut, fin) de la ligne mediane de chaque role, en pixels de la texture
ROLES = [
    # Nonexistent Youth
    ((183, 288), (321, 337), LYR_COMP),
    ((119, 324), (208, 353), ARR),
    ((141, 354), (202, 373), SUNG),
    # Vanitas of the Lunar Eclipse
    ((752, 370), (796, 367), LYR),
    ((754, 387), (939, 372), COMP_ARR),
    ((760, 427), (812, 423), SUNG),
    # Silent Wind Bell
    ((1352, 220), (1387, 212), LYR),
    ((1344, 263), (1417, 243), COMP),
    ((1356, 302), (1428, 282), ARR),
    ((1380, 337), (1427, 323), SUNG),
    # Singularity
    ((1921, 222), (2076, 262), LYR_COMP),
    ((1935, 273), (2037, 302), ARR),
    ((1942, 323), (2007, 343), SUNG),
]


def _encre(a, y0, y1, x0, x1):
    """L'encre sur le papier : plus sombre que le papier alentour (mediane
    locale), le papier variant d'une etiquette a l'autre."""
    lum = a[y0:y1, x0:x1, :3].mean(axis=2)
    fond = np.asarray(Image.fromarray(np.clip(lum, 0, 255).astype("uint8"))
                      .filter(ImageFilter.MedianFilter(15)), dtype=float)
    return lum < fond - 45


def role(a, p, q, en, fr):
    (xa, ya), (xb, yb) = p, q
    M = 30
    y0, y1 = max(0, min(ya, yb) - M), max(ya, yb) + M
    x0, x1 = max(0, min(xa, xb) - M), max(xa, xb) + M + 60
    z = a[y0:y1, x0:x1]
    encre = _encre(a, y0, y1, x0, x1)

    # repere de la ligne : u le long, v en travers
    d = np.array([xb - xa, yb - ya], float)
    L = np.hypot(*d)
    d /= L
    n = np.array([-d[1], d[0]])
    yy, xx = np.mgrid[y0:y1, x0:x1]
    u = (xx - xa) * d[0] + (yy - ya) * d[1]
    v = (xx - xa) * n[0] + (yy - ya) * n[1]

    # A cette taille, le seuil casse les lettres en miettes : on ne trie pas
    # composante par composante, on prend toute l'encre du rectangle tourne
    # du role (points des i au-dessus, queues des g et des y au-dessous,
    # deux-points au-dela), jusqu'au nom qui suit sur la ligne, et on en
    # retire ce qui appartient aux voisins.
    lab, infos = composantes.composantes(encre)
    apres = []                                 # le nom qui suit sur la ligne
    voisins = np.zeros(encre.shape, bool)      # lettres des autres lignes
    tirets = np.zeros(encre.shape, bool)       # tirets imprimes (etiquette 1)
    miettes = []
    for i, inf in enumerate(infos, 1):
        m = lab == i
        cu, cv = u[m].mean(), v[m].mean()
        if inf[0] >= 8:
            if abs(cv) > 7:
                voisins |= m
            elif cu > L + 6:
                apres.append(u[m].min())
        elif cv < -6 and np.ptp(u[m]) + 1 > 1.6 * (np.ptp(v[m]) + 1) + 1:
            tirets |= m
        elif cv > 5:
            miettes.append(m)
    # sous l'axe, un point rond colle a une lettre de la ligne du dessous est
    # le point d'un i de cette ligne, pas la queue d'un g ou d'un y du role
    pres = rebouche.dilate(voisins, 3)
    for m in miettes:
        eu, ev = np.ptp(u[m]) + 1, np.ptp(v[m]) + 1
        if (m & pres).any() and ev <= 4 and eu <= 1.6 * ev + 1:
            voisins |= m
    fin = min(apres) - 7 if apres else None
    bout = min(L + 12, fin + 4) if fin is not None else L + 12
    garde = (encre & (u >= -6) & (u <= bout) & (v >= -13) & (v <= 13)
             & ~voisins & ~tirets)

    angle0 = np.degrees(np.arctan2(d[1], d[0]))
    px = z[garde][:, :3]
    l = px.mean(axis=1)
    # lettres de 1 ou 2 px : seul le decile le plus sombre est de l'encre pure
    couleur = px[l <= np.percentile(l, 10)].mean(axis=0)

    # gommage : la diffusion ne voit pas les autres encres (noms, cadre)
    trou = rebouche.dilate(garde, 1)
    fond = z[..., :3].copy()
    autre = encre & ~garde
    papier = ~encre & ~rebouche.dilate(encre, 1)
    fond[autre] = np.median(z[papier][:, :3], axis=0)
    fond = rebouche.diffuse(fond, trou, 300)
    z[trou, :3] = fond[trou]

    # Le masque est trop bruite pour chercher la rotation par recouvrement :
    # l'angle est l'axe principal de l'encre, l'echelle le rapport des
    # longueurs le long de la ligne. Seule la position est ajustee : on cale
    # l'origine du texte (debut de ligne, ligne de base) de l'anglais rendu
    # sur l'encre, et le francais part du meme point.
    ys, xs = np.nonzero(garde)
    c = np.cov(np.vstack([xs, ys]).astype(float))
    vp = np.linalg.eigh(c)[1][:, -1]
    theta = np.degrees(np.arctan2(vp[1], vp[0]))
    if theta - angle0 > 90:
        theta -= 180
    elif angle0 - theta > 90:
        theta += 180
    if abs(theta - angle0) > 5:
        theta = angle0
    ug = u[garde]
    etendue = np.percentile(ug, 99.5) - np.percentile(ug, 0.5)
    s = etendue / float(_largeur(en))

    ge, eo = _rendu_tourne(en, s, theta)
    poids = garde.astype(float) - 0.3
    sc = localise._correle(poids, ge)
    iy, ix = divmod(int(np.argmax(sc)), sc.shape[1])
    oy, ox = iy + eo[1], ix + eo[0]            # origine, dans z

    serre = 1.0
    if fin is not None:
        u_o = (x0 + ox - xa) * d[0] + (y0 + oy - ya) * d[1]
        place = fin - u_o
        long_fr = _largeur(fr) * s
        if long_fr > place:
            serre = place / long_fr
    g, fo = _rendu_tourne(fr, s, theta, serre)
    h, w = g.shape
    Y, X = y0 + oy - fo[1], x0 + ox - fo[0]
    b = a[Y:Y + h, X:X + w, :3]
    b[:] = b * (1 - g[..., None]) + couleur * g[..., None]
    print("   %-24s -> %-26s angle %+.1f, echelle %.3f%s"
          % (en, fr, theta, s, ", resserre %.2f" % serre if serre < 1 else ""))


def _largeur(texte):
    """Largeur de l'encre du texte, au corps de travail."""
    g = habillage._rendu(texte, GARAMOND)[0]
    return g.shape[1]


def _rendu_tourne(texte, s, theta, serre=1.0):
    """Le texte a l'echelle s, tourne de theta degres, resserre de `serre` ;
    rend (couverture, (x, y) de l'origine du texte dans la couverture)."""
    G = habillage.G
    ft = ImageFont.truetype(GARAMOND, G)
    im = Image.new("L", (int(G * (len(texte) + 2)), G * 3), 0)
    habillage.ecrit(ImageDraw.Draw(im), G, 2 * G, texte, ft, anchor="ls")
    # la reduction d'abord, lissee (une transformation bicubique ne lisse pas
    # en reduction), puis la rotation seule
    W0 = max(1, int(round(im.width * s * serre)))
    H0 = max(1, int(round(im.height * s)))
    o = np.array([G * W0 / float(im.width), 2.0 * G * H0 / float(im.height)])
    im = im.resize((W0, H0), Image.LANCZOS)
    t = np.radians(theta)
    A = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
    w, h = im.size
    coins = A.dot(np.array([[0, w, 0, w], [0, 0, h, h]], float))
    mn = coins.min(axis=1)
    W = int(np.ceil(coins[0].max() - mn[0])) + 2
    H = int(np.ceil(coins[1].max() - mn[1])) + 2
    inv = np.linalg.inv(A)
    cf = (inv[0, 0], inv[0, 1], inv[0, 0] * mn[0] + inv[0, 1] * mn[1],
          inv[1, 0], inv[1, 1], inv[1, 0] * mn[0] + inv[1, 1] * mn[1])
    r = np.asarray(im.transform((W, H), Image.AFFINE, cf, resample=Image.BICUBIC),
                   dtype=float) / 255.0
    oo = A.dot(o) - mn
    ys, xs = np.nonzero(r > 0.02)
    r = r[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return r, (int(round(oo[0] - xs.min())), int(round(oo[1] - ys.min())))


# ------------------------------------------------------------ titres en relief

ARRONDIE = "C:/Windows/Fonts/ARLRDBD.TTF"
R_HAUT, R_BAS, R_REF = 225.0, 120.0, 170.0     # l'anneau deroule
# (centre du disque de metal, colonnes du titre dans la bande deroulee,
#  anglais, francais) ; colonne 0 = gauche de la bobine, sens horaire
REBORDS = [
    ((270.5, 272.9), (155, 507), "Original Opening Movie", "Opening original"),
    ((850.4, 271.2), (45, 403), "Normal Ending Credits", u"G\u00e9n\u00e9rique \u2013 fin normale"),
    ((1428.8, 275.6), (340, 658), "True Ending Credits", u"G\u00e9n\u00e9rique \u2013 vraie fin"),
    ((2008.6, 274.7), (238, 472), "Opening Movie", "Opening"),
]
LIGNES = (36, 86)                               # rangees du titre dans la bande


def _echantillonne(img, X, Y):
    """Lecture bilineaire de img (h, w, c) aux positions X, Y."""
    x0 = np.clip(np.floor(X).astype(int), 0, img.shape[1] - 2)
    y0 = np.clip(np.floor(Y).astype(int), 0, img.shape[0] - 2)
    fx = (X - x0)[..., None]
    fy = (Y - y0)[..., None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


def deroule(a, centre):
    """L'anneau en bande droite : une colonne par pixel d'arc au rayon de
    reference, une rangee par pixel de rayon (exterieur en haut)."""
    cx, cy = centre
    n = int(round(2 * np.pi * R_REF))
    phi = -np.pi + np.arange(n) / R_REF
    r = R_HAUT - np.arange(int(R_HAUT - R_BAS))
    P, R = np.meshgrid(phi, r)
    return _echantillonne(a[..., :3], cx + R * np.cos(P), cy + R * np.sin(P))


# les plages de gorge propre (ni texte ni papier d'etiquette) entre les
# rangees LIGNES, relevees sur les bandes deroulees
PROPRES = [[(30, 150), (510, 575)], [(5, 40), (410, 500)], [(665, 880)], [(560, 930)]]


def rapiece(cible, x0, x1, y0, y1, sources, T=32, R=8):
    """Rebouche [x0, x1] de gauche a droite, par morceaux de T colonnes pris
    dans les gorges libres des quatre bobines (memes rayons, donc memes
    sillons) : chaque morceau est celui qui se raccorde le mieux au
    precedent sur R colonnes, fondues. Le dernier se raccorde aussi au bord
    droit, et les bords haut et bas de la zone sont fondus avec l'original."""
    out = cible.copy()
    x = x0
    while x <= x1:
        w = min(T, x1 - x + 1)
        dernier = x + w > x1
        avant = out[y0:y1, x - R:x]
        apres = cible[y0:y1, x1 + 1:x1 + 1 + R]
        meilleur = None
        for bande, plages in sources:
            # la meme bobine d'abord : la teinte de la rouille varie de l'une
            # a l'autre
            penalite = 1.0 if bande is cible else 1.3
            for d, f in plages:
                for sx in range(d + R, f - w - R + 2, 2):
                    src = bande[y0:y1, sx - R:sx + w + R]
                    dec = np.clip((avant - src[:, :R]).mean(axis=(0, 1)), -25, 25)
                    cout = ((src[:, :R] + dec - avant) ** 2).mean()
                    if dernier:
                        cout += ((src[:, R + w:] + dec - apres) ** 2).mean()
                    cout *= penalite
                    if meilleur is None or cout < meilleur[0]:
                        meilleur = (cout, src + dec)
        src = meilleur[1]
        t = np.linspace(0, 1, R + 2)[1:-1][None, :, None]
        out[y0:y1, x - R:x] = avant * (1 - t) + src[:, :R] * t
        out[y0:y1, x:x + w] = src[:, R:R + w]
        if dernier:
            out[y0:y1, x1 + 1:x1 + 1 + R] = src[:, R + w:] * (1 - t) + apres * t
        x += w
    F = 6
    for k in range(F):
        t = (k + 1) / float(F + 1)
        for yy in (y0 + k, y1 - 1 - k):
            out[yy, x0:x1 + 1] = cible[yy, x0:x1 + 1] * (1 - t) + out[yy, x0:x1 + 1] * t
    return out


# le relief des titres d'origine : lisere sombre en haut a gauche, reflet
# clair en bas a droite, remplissage dore qui laisse voir la rouille
RELIEF = dict(ombre=(-1.0, 0.8, 1.0, (30.0, 20, 12)),
              reflet=(1.6, 0.6, 0.6, (235.0, 228, 212)),
              texture=(0.6, 1.4, 0.8))
# la couleur des lettres : doree, argentee sur la quatrieme bobine
REMPLIS = [(172.0, 146, 102), (172.0, 146, 102), (172.0, 146, 102), (208.0, 202, 190)]


def relief(bande, g, x, y, fond_l, rempli):
    """Pose le masque g en relief, dans la bande deroulee."""
    h, w = g.shape
    M = 5
    G = np.zeros((h + 2 * M, w + 2 * M))
    G[M:M + h, M:M + w] = g
    im = Image.fromarray((G * 255).astype("uint8"))

    epais = im.filter(ImageFilter.MaxFilter(3))

    def decale(d, flou):
        src = epais if d < 0 else im           # le lisere sombre, un peu gras
        r = src.transform(src.size, Image.AFFINE, (1, 0, -d, 0, 1, -d),
                          resample=Image.BILINEAR).filter(ImageFilter.GaussianBlur(flou))
        return np.clip(np.asarray(r, dtype=float) / 255.0 * 1.2, 0, 1)

    b = bande[y - M:y + h + M, x - M:x + w + M]
    for cle in ("ombre", "reflet"):
        d, flou, force, coul = RELIEF[cle]
        m = decale(d, flou)[..., None] * force
        b[:] = b * (1 - m) + np.array(coul) * m
    tmin, tmax, gam = RELIEF["texture"]
    lum = b.mean(axis=2, keepdims=True)
    tex = np.clip(lum / max(fond_l, 1.0), tmin, tmax) ** gam
    b[:] = b * (1 - G[..., None]) + np.array(rempli) * tex * G[..., None]


def rebord(a, centre, cols, en, fr, bande, sources, rempli):
    x0, x1 = cols
    y0, y1 = LIGNES
    neuf = rapiece(bande, x0 - 4, x1 + 4, y0, y1, sources)
    fond_l = bande[y0:y1].mean()

    # le francais : meme echelle que l'anglais, centre sur lui, meme ligne
    # de base
    ge, te, _, base = habillage._rendu(en, ARRONDIE)
    gf, tf, _, _ = habillage._rendu(fr, ARRONDIE)
    s = (x1 - x0 + 1) / float(ge.shape[1])
    W = max(1, int(round(gf.shape[1] * s)))
    H = max(1, int(round(gf.shape[0] * s)))
    g = np.asarray(Image.fromarray((gf * 255).astype("uint8")).resize((W, H), Image.LANCZOS),
                   dtype=float) / 255.0
    he = int(round(ge.shape[0] * s))
    haut_en = int(round((y0 + y1) / 2.0 - he / 2.0))
    yb = haut_en + (base - te) * s
    y = int(round(yb - (base - tf) * s))
    x = int(round((x0 + x1) / 2.0 - W / 2.0))
    relief(neuf, g, x, y, fond_l, rempli)

    zone = np.zeros(bande.shape[:2])
    zone[y0:y1, min(x0 - 4, x - 6):max(x1 + 4 + 8, x + W + 6) + 1] = 1.0
    enroule(a, centre, neuf, zone)
    print("   %-24s -> %-26s %3d px d'arc (anglais %3d)" % (en, fr, W, x1 - x0 + 1))


def enroule(a, centre, bande, zone):
    """Reporte la bande sur l'anneau, la ou `zone` vaut 1."""
    cx, cy = centre
    Y, X = np.mgrid[int(cy - R_HAUT) - 1:int(cy + R_HAUT) + 2,
                    int(cx - R_HAUT) - 1:int(cx + R_HAUT) + 2]
    dx, dy = X - cx, Y - cy
    r = np.hypot(dx, dy)
    phi = np.arctan2(dy, dx)
    col = (phi + np.pi) * R_REF
    row = R_HAUT - r
    dedans = (row >= 0) & (row <= bande.shape[0] - 2)
    Xs, Ys = X[dedans], Y[dedans]
    c, w = col[dedans], row[dedans]
    poids = _echantillonne(zone[..., None], c % (bande.shape[1] - 1), w)[..., 0]
    ok = poids > 0.5
    v = _echantillonne(bande, c[ok] % (bande.shape[1] - 1), w[ok])
    a[Ys[ok], Xs[ok], :3] = v


def menu(a):
    avant = a.copy()
    habillage.bandeau(a, (1171, 1219), (1179, 1209), [
        ((110, 196, 234), "SELECT", "CHOISIR"),
        ((271, 386, 423), "CONFIRM", "VALIDER"),
        ((467, 530, 1100), "BACK", "RETOUR"),
    ])
    for p, q, (en, fr) in ROLES:
        role(a, p, q, en, fr)
    bandes = [deroule(a, centre) for centre, _, _, _ in REBORDS]
    sources = list(zip(bandes, PROPRES))
    for b, (centre, cols, en, fr), rempli in zip(bandes, REBORDS, REMPLIS):
        rebord(a, centre, cols, en, fr, b, sources, rempli)
    rangee_du_bas(a, avant)
    return a


def rangee_du_bas(a, avant, haut=560, large=2310):
    """Reporte sur la rangee du bas ce qui a change dans celle du haut, sauf
    sous la peinture rouge."""
    neuf = a[0:haut, 0:large].astype(float)
    vieux = avant[0:haut, 0:large].astype(float)
    bas = a[DECALE:DECALE + haut, 0:large]
    delta = neuf - vieux
    change = np.abs(delta).max(axis=2) > 0
    rouge = (bas[..., 0] > 150) & (bas[..., 1] < 100) & (bas[..., 2] < 90)
    ok = change & ~rebouche.dilate(rouge, 1) & (bas[..., 3] > 0)
    bas[ok] = np.clip(bas[ok] + delta[ok], 0, 255)
