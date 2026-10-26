# -*- coding: utf-8 -*-
"""L'ecran titre : title_chip (les entrees du menu, le bandeau, PRESS ENTER)
et title_bg (la phrase d'accroche sous le logo).

Les entrees sont des sprites decoupes au plus pres par le jeu, dans des
rectangles qu'on ne peut pas elargir : le francais doit tenir dans la boite
de l'anglais (la colonne principale, elle, est decoupee a la largeur de
NEW GAME pour toutes ses entrees). L'original est en Helvetica Bold ; on la
remplace par TeX Gyre Heros Bold (licence GUST), de memes dessins.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import carte
import composantes
import habillage
import rebouche

HEROS = carte.police("texgyreheros-bold.otf")
HEROS_ETROITE = carte.police("texgyreheroscn-bold.otf")
BLANC = (255.0, 255, 255)
NOIR = (0.0, 0, 0)
ORANGE = (230.0, 79, 51)
GRAISSE = 8                # au corps G = 300 ; calee sur TIPS, CONTINUE, LIBRARY
SERRE = 0.83             # resserrement tolere (en Heros, puis en etroite)

# (boite de l'encre anglaise (y0, y1, x0, x1), couleur, anglais, francais,
#  largeur permise)
PRINCIPALE = 213
ENTREES = [
    ((324, 351, 4, 112), BLANC, "TRUE", "VRAIE FIN", PRINCIPALE),
    ((360, 387, 5, 217), BLANC, "NEW GAME", "COMMENCER", PRINCIPALE),
    ((396, 423, 5, 212), BLANC, "CONTINUE", "CONTINUER", PRINCIPALE),
    ((432, 459, 6, 143), BLANC, "EXTRA", "BONUS", PRINCIPALE),
    ((468, 495, 5, 153), BLANC, "CONFIG", "OPTIONS", PRINCIPALE),
    ((504, 531, 6, 108), BLANC, "HELP", "AIDE", PRINCIPALE),
]
for _y, _c in ((324, NOIR), (360, ORANGE)):
    ENTREES.append(((_y, _y + 29, 231, 470), _c, "QUICK LOAD", "CHARGEMENT RAPIDE", 240))
    ENTREES.append(((_y, _y + 27, 488, 581), _c, "TIPS", "TIPS", 94))
for _y, _c in ((396, NOIR), (432, ORANGE)):
    ENTREES.append(((_y, _y + 27, 233, 333), _c, "LOAD", "CHARGER", 101))
    ENTREES.append(((_y, _y + 27, 489, 655), _c, "LIBRARY", "GALERIE", 167))
for _y, _c in ((468, NOIR), (504, ORANGE)):
    ENTREES.append(((_y, _y + 27, 488, 732), _c, "ENDING LIST", "LISTE DES FINS", 245))


def _rendu(texte, police, graisse=None):
    """habillage._rendu, les traits epaissis de `graisse` (au corps G) :
    l'original est plus gras que la Heros Bold."""
    if graisse is None:
        graisse = GRAISSE
    G = habillage.G
    ft = ImageFont.truetype(police, G)
    im = Image.new("L", (int(G * (len(texte) + 2)), G * 3), 0)
    ImageDraw.Draw(im).text((G, G), texte, 255, font=ft, stroke_width=graisse, stroke_fill=255)
    x0, y0, x1, y1 = im.getbbox()
    base = G + ft.getbbox("H")[3]
    return np.asarray(im.crop((x0, y0, x1, y1)), dtype=float) / 255.0, y0, x0, base


def _mot(en, fr, boite, largeur):
    """Le francais a l'echelle et a la chasse de l'anglais en Heros ; s'il
    deborde, en Heros etroite, puis resserre : la hauteur ne change pas."""
    y0, y1, x0, x1 = boite
    ge, te, le, base = _rendu(en, HEROS)
    ey0, ey1, ex0, ex1 = habillage._encre(ge > 0.5)
    k = (y1 - y0 + 1) / float(ey1 - ey0 + 1)
    c = (x1 - x0 + 1) / float((ex1 - ex0 + 1) * k)
    base_img = y0 + (base - (te + ey0)) * k
    for police in (HEROS, HEROS_ETROITE):
        gf, tf, lf, bf = _rendu(fr, police)
        fy0, fy1, fx0, fx1 = habillage._encre(gf > 0.02)
        gf = gf[fy0:fy1 + 1, fx0:fx1 + 1]
        if gf.shape[1] * k * c * SERRE <= largeur:
            break
    # au-dela de SERRE, les lettres se deforment (NOUVELLE PARTIE l'etait a
    # 0,73 dans le jeu) : on reduit plutot le corps, centre sur les capitales
    cf = max(min(c, largeur / (gf.shape[1] * k)), c * SERRE)
    kf = min(k, largeur / (gf.shape[1] * cf))
    base_img -= (k - kf) * (ey1 - ey0 + 1) / 2.0
    W = max(1, int(round(gf.shape[1] * kf * cf)))
    H = max(1, int(round(gf.shape[0] * kf)))
    g = np.asarray(Image.fromarray((gf * 255).astype("uint8")).resize((W, H), Image.LANCZOS),
                   dtype=float) / 255.0
    haut = int(round(base_img - (bf - (tf + fy0)) * kf))
    return g, haut, x0, police, cf / c, kf / k


def entree(a, boite, couleur, en, fr, largeur):
    """Remplace un mot du menu, lettres pleines sur fond transparent."""
    y0, y1, x0, x1 = boite
    a[y0 - 3:y1 + 4, x0 - 3:x1 + 4, 3] = 0.0
    g, y, x, police, serre, reduit = _mot(en, fr, boite, largeur)
    h, w = g.shape
    b = a[y:y + h, x:x + w]
    b[..., 3] = np.maximum(b[..., 3], g * 255.0)
    a[y0 - 3:y1 + 4, x0 - 3:x1 + 4, :3] = couleur
    print("   %-11s -> %-18s %3d px (anglais %3d)%s%s%s"
          % (en, fr, w, x1 - x0 + 1, ", etroite" if police == HEROS_ETROITE else "",
             ", serre x%.2f" % serre if serre < 0.99 else "",
             ", corps x%.2f" % reduit if reduit < 0.99 else ""))


def menu(a):
    for boite, couleur, en, fr, largeur in ENTREES:
        entree(a, boite, couleur, en, fr, largeur)
    return a


# ------------------------------------------------------------ title_bg
# La phrase d'accroche sous le logo, posee par le Committee of Zero sur le
# fond (a la place de l'anglais approximatif de l'original), en deux
# exemplaires : le fond normal (en haut) et celui de la vraie fin (en bas,
# une ligne plus haut). Le fond est rebouche avec l'original japonais de
# system.mpk, dont l'accroche n'est pas aux memes endroits : sous une lettre
# anglaise, on reprend le japonais ; la ou les deux se recouvrent, le fond
# un peu plus bas.

SYSTEME = "D:/SteamLibrary/steamapps/common/CHAOS;CHILD/USRDIR/system.mpk"
GARAMOND = carte.police("EBGaramond-Medium.ttf")
ENCRE = (41.0, 40, 41)
ACCROCHE = [u"Si tu étais Dieu, et que tes délusions pouvaient devenir réalité, "
            u"lesquelles souhaiterais-tu\u2009?",
            u"Un monde sensuel\u2009? Une société despotique\u2009? "
            u"Des sanctions destructives\u2009? Ou\u2026"]
# (decalage vertical, lignes de base, centres) ; hauteur d'x 11 px
EXEMPLAIRES = [(0, (427.5, 455.0)), (864, (426.5, 454.0))]
CENTRES = (2825, 2841)
HAUTEUR_X = 11.0
BANDE = (403, 466, 2350, 3300)
# decalages verticaux du fond de remplacement : des multiples de la
# periode de la trame de points (10,67 px), sous la bande du texte
DECALAGES = (64, 96, 128, 160, 192)


def japonais(nom):
    """Le fichier `nom` de system.mpk (l'original), mis en cache."""
    import io
    import os
    import mpk
    dossier = os.path.join(os.path.dirname(carte.RACINE), "reference", "system")
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    c = os.path.join(dossier, nom)
    if not os.path.exists(c):
        f = io.open(SYSTEME, "rb")
        T = dict((e.nom, e) for e in mpk.lit_table(f) if e.nom)
        io.open(c, "wb").write(mpk.lit(f, T[nom]))
    return c


def _ferme(m, r):
    return ~rebouche.dilate(~rebouche.dilate(m, r), r)


def fond(a, j, off, autres=()):
    """Efface l'accroche anglaise de l'exemplaire decale de `off` ; `autres` :
    des decalages de remplacement en plus (vers l'autre exemplaire, deja
    nettoye)."""
    y0, y1, x0, x1 = BANDE
    y0, y1 = y0 + off, y1 + off
    z = a[y0:y1, x0:x1, :3]
    zj = j[y0:y1, x0:x1, :3]
    lc, lj = z.mean(axis=2), zj.mean(axis=2)
    # le fond local : le plus clair des deux, au maximum sur 7 px (les
    # lettres y disparaissent)
    clair = Image.fromarray(np.maximum(lc, lj).astype("uint8")).filter(ImageFilter.MaxFilter(7))
    clair = np.asarray(clair, dtype=float)
    sombres = (clair - lc > 25) & (clair - lj > 25)      # lettres, planches, points
    anglais = rebouche.dilate((lj - lc) > 8, 1)
    anglais |= sombres & rebouche.dilate(anglais, 3)
    japon = rebouche.dilate((lc - lj) > 8, 1) | rebouche.dilate(sombres, 1)
    # le Committee of Zero a retouche le fond par endroits : le japonais est
    # ramene au ton de l'anglais par l'ecart releve autour des deux textes
    ton = rebouche.diffuse(z - zj, anglais | japon, 300)
    pris = anglais & ~japon
    z[pris] = np.clip(zj[pris] + ton[pris], 0, 255)
    # sous les deux accroches a la fois : les memes colonnes, un nombre
    # entier de periodes de la trame plus bas (les planches et les points
    # tombent juste), le decalage qui raccorde le mieux et n'apporte pas de
    # tache sombre ; fondu au pourtour (on diffuse l'ecart au bord, a la
    # Poisson)
    trou = anglais & japon
    lab, comps = composantes.composantes(trou)
    for i, (n, cy0, cy1, cx0, cx1) in enumerate(comps):
        Y0, Y1 = max(0, cy0 - 2), min(z.shape[0], cy1 + 3)
        X0, X1 = max(0, cx0 - 2), min(z.shape[1], cx1 + 3)
        m = lab[Y0:Y1, X0:X1] == i + 1
        bord = rebouche.dilate(m, 1) & ~m
        zz = z[Y0:Y1, X0:X1]
        ref = np.median(zz[bord].mean(axis=1)) if bord.any() else 200.0
        meilleur = None
        for dy in DECALAGES + tuple(autres):
            src = a[y0 + Y0 + dy:y0 + Y1 + dy, x0 + X0:x0 + X1, :3]
            e = zz - src
            cout = e[bord].var(axis=0).sum() if bord.any() else 0.0
            cout += 1e4 * (src[m].mean(axis=1) < ref - 50).mean()
            if meilleur is None or cout < meilleur[0]:
                meilleur = (cout, src)
        src = meilleur[1]
        ecart = rebouche.diffuse(zz - src, m, 300)
        zz[m] = np.clip(src[m] + ecart[m], 0, 255)
    return trou.sum()


def _phrase(texte, hauteur_x, largeur_max):
    """Une ligne en Garamond, a la hauteur d'x voulue ; rend la couverture et
    la hauteur de sa ligne de base au-dessous de son bord haut."""
    G = habillage.G
    ft = ImageFont.truetype(GARAMOND, G)
    im = Image.new("L", (int(G * len(texte)), G * 3), 0)
    ImageDraw.Draw(im).text((G, G), texte, 255, font=ft, anchor="ls")
    bx0, by0, bx1, by1 = im.getbbox()
    gf = np.asarray(im.crop((bx0, by0, bx1, by1)), dtype=float) / 255.0
    hx = ft.getbbox("x", anchor="ls")
    k = hauteur_x / float(hx[3] - hx[1])
    c = min(1.0, largeur_max / (gf.shape[1] * k))
    W, H = int(round(gf.shape[1] * k * c)), int(round(gf.shape[0] * k))
    g = np.asarray(Image.fromarray((gf * 255).astype("uint8")).resize((W, H), Image.LANCZOS),
                   dtype=float) / 255.0
    return g, (G - by0) * k


def accroche(a, off, bases, largeur_max=950):
    for texte, base, centre in zip(ACCROCHE, bases, CENTRES):
        g, by0 = _phrase(texte, HAUTEUR_X, largeur_max)
        h, w = g.shape
        y = int(round(base + off - by0))
        x = int(round(centre - w / 2.0))
        b = a[y:y + h, x:x + w, :3]
        b[:] = b * (1 - g[..., None]) + np.array(ENCRE) * g[..., None]
        print("   accroche %s : %d px" % ("vraie fin" if off else "normale", w))


def titre_bg(a):
    """Le fond de la vraie fin d'abord : sous l'accroche du fond normal
    tombent des pierres, sur toutes les lignes de remplacement ; on y prend
    alors l'autre exemplaire (81 periodes de la trame plus bas)."""
    import dds
    j = dds.lit(japonais("title_bg.dds"))["rgba"].astype(float)
    for off, autres in ((864, ()), (0, (864,))):
        n = fond(a, j, off, autres)
        print("   %d px recouverts par les deux accroches, rebouches" % n)
    for off, bases in EXEMPLAIRES:
        accroche(a, off, bases)
    return a


# ------------------------------------------------------------ title_chip
HATTEN = habillage.HATTEN
BANDEAU = ((606, 655), (615, 644), [
    ((110, 196, 234), "SELECT", "CHOISIR"),
    ((271, 386, 423), "CONFIRM", "VALIDER"),
    ((467, 530, 1100), "BACK", "RETOUR"),
])


def presse(a):
    """PRESS ENTER, en blanc sur la tache orange ; le sprite s'arrete a
    x 1812, la tache ne peut pas s'elargir."""
    z = a[700:780, 1530:1790]
    lettres = (z[..., :3].min(axis=2) > 200) & (z[..., 3] > 200)
    trou = rebouche.dilate(lettres, 2) & (z[..., 3] > 250)
    z[trou, :3] = ORANGE
    g, y, x = habillage.comme("PRESS ENTER", u"APPUYEZ SUR ENTRÉE", HATTEN,
                              (724, 749, 1564, 1751), largeur_max=240)
    h, w = g.shape
    x = int(round((1564 + 1751) / 2.0 - w / 2.0))
    b = a[y:y + h, x:x + w, :3]
    b[:] = b * (1 - g[..., None]) + 255.0 * g[..., None]
    print("   PRESS ENTER -> APPUYEZ SUR ENTRÉE %d px (anglais 188)" % w)
    # sous la main, l'utilisateur actif (des consoles) : blanc sur fond
    # transparent
    a[783:803, 1692:1778, 3] = 0.0
    g, y, x = habillage.comme("ACTIVE USER", "UTILISATEUR ACTIF", HATTEN,
                              (786, 799, 1695, 1773), largeur_max=1810 - 1695)
    h, w = g.shape
    b = a[y:y + h, x:x + w]
    b[..., 3] = np.maximum(b[..., 3], g * 255.0)
    a[783:803, 1692:1812, :3] = 255.0
    print("   ACTIVE USER -> UTILISATEUR ACTIF %d px (anglais 79)" % w)


# l'accroche sous le logo du sprite (anglais approximatif de l'original) :
# noire, dans l'alpha. Le jeu affiche celle de title_bg ; on traduit
# celle-ci aussi, pour le cas ou.
ACCROCHE_LOGO = ((969, 1022, 30, 936), (988.0, 1013.0), (482, 472))


def accroche_logo(a):
    (y0, y1, x0, x1), bases, centres = ACCROCHE_LOGO
    a[y0:y1, x0:x1, 3] = 0.0
    for texte, base, centre in zip(ACCROCHE, bases, centres):
        g, by0 = _phrase(texte, HAUTEUR_X - 0.5, 900)
        h, w = g.shape
        y = int(round(base - by0))
        x = int(round(centre - w / 2.0))
        b = a[y:y + h, x:x + w]
        b[..., 3] = np.maximum(b[..., 3], g * 255.0)
    a[y0:y1, x0:x1, :3] = 0.0


def titre_chip(a):
    menu(a)
    habillage.bandeau(a, *BANDEAU)
    presse(a)
    accroche_logo(a)
    return a
