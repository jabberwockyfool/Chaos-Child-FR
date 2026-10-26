# -*- coding: utf-8 -*-
"""L'habillage commun des ecrans de menu, et les ecrans qui l'utilisent.

Les menus de sauvegarde (loadmenu, savemenu, qloadmenu) ont la meme mise en
page, seuls changent le grand logo, l'onglet et les couleurs ; le journal
(backlog) reprend le bandeau et le logo. Quatre sortes de texte :

- le bandeau du bas (SELECT, CONFIRM...) : Haettenschweiler blanc sur un
  degrade rouge purement horizontal, rebouche par diffusion ;
- le grand logo : Haettenschweiler plein, rempli d'une texture grunge et
  entoure d'un halo noir. La texture des nouvelles lettres est prise dans
  celle des anciennes, decalee d'une chasse de lettre ;
- NO DATA / DATA BROKEN : Chiller blanc sur une tache de bombe noire ;
- SAVETIME, LOCKED : Haettenschweiler brun, le texte dans l'alpha.

Pour chaque libelle, on rend l'anglais dans la police et on le cale sur
l'encre de l'original : ca donne l'echelle, la chasse et la ligne de base, que
le francais reprend. Trop large, il est resserre jusqu'a 75 % de la chasse
d'origine, puis seulement reduit, sur la meme ligne de base.

Le jeu decoupe chaque element a son rectangle de sprite. Ceux du logo et de
l'onglet ne sont pas dans les fichiers du patch ; comme les trois menus
partagent la mise en page, on suppose qu'ils couvrent ceux de QUICK LOAD, le
plus large : 1044 px pour le logo, 150 px pour l'onglet. A verifier en jeu.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import composantes
import rebouche

HATTEN = "C:/Windows/Fonts/HATTEN.TTF"
CHILLER = "C:/Windows/Fonts/CHILLER.TTF"
FRANKLIN = "C:/Windows/Fonts/FRAHV.TTF"
G = 300                  # corps de travail des rendus
SERRE_MIN = 0.75         # resserrement maximal, relatif a l'original

LOGO = {
    "loadmenu.dds": ("LOAD", "CHARGER"),
    "savemenu.dds": ("SAVE", "SAUVEGARDER"),
    "qloadmenu.dds": ("QUICK LOAD", "CHARGEMENT RAPIDE"),
}
LOGO_X, LOGO_LARGE = 11, 1044
ONGLET_X, ONGLET_LARGE = 1242, 150

# (debut, fin du mot anglais, debut de l'icone suivante), anglais, francais
BANDEAU = [
    ((110, 196, 234), "SELECT", "CHOISIR"),
    ((271, 386, 423), "CONFIRM", "VALIDER"),
    ((475, 605, 643), "LOCK DATA", "PROTÉGER"),
    ((687, 751, 1100), "BACK", "RETOUR"),
]


# ---------------------------------------------------------------- rendu

# crenage a la main : sans libraqm, Pillow ignore celui de certaines polices
CRENAGE = {"/A": -0.10}


def ecrit(d, x, y, texte, ft, anchor=None):
    """ImageDraw.text, avec le crenage de CRENAGE."""
    debut = 0
    for i in range(1, len(texte)):
        k = CRENAGE.get(texte[i - 1:i + 1])
        if k:
            morceau = texte[debut:i]
            d.text((x, y), morceau, 255, font=ft, anchor=anchor)
            x += ft.getlength(morceau) + k * ft.size
            debut = i
    d.text((x, y), texte[debut:], 255, font=ft, anchor=anchor)


def _rendu(texte, police):
    """Le texte a G px, sur une origine fixe : (couverture, haut, gauche,
    ligne de base), les trois derniers dans le repere du rendu."""
    ft = ImageFont.truetype(police, G)
    im = Image.new("L", (int(G * (len(texte) + 2)), G * 3), 0)
    ecrit(ImageDraw.Draw(im), G, G, texte, ft)
    x0, y0, x1, y1 = im.getbbox()
    base = G + ft.getbbox("H")[3]
    return np.asarray(im.crop((x0, y0, x1, y1)), dtype=float) / 255.0, y0, x0, base


def _encre(m):
    ys, xs = np.nonzero(m)
    return ys.min(), ys.max(), xs.min(), xs.max()


def comme(en, fr, police, boite, largeur_max=None, seuil=0.5, plafond=None,
          reduit=1.0):
    """Le francais a l'echelle de l'anglais trouve dans `boite`.

    `boite` = (y0, y1, x0, x1), l'encre de l'original, bornes incluses.
    Rend (g, y, x) : la couverture et son coin haut gauche, cale a gauche sur
    l'anglais et sur sa ligne de base.

    `plafond` : la ligne que les accents ne doivent pas depasser (un sprite
    decoupe au plus pres) ; au besoin, le mot est reduit sur sa ligne de base.
    `reduit` : un facteur de reduction impose, pour garder une serie de
    libelles a la meme taille.
    """
    y0, y1, x0, x1 = boite
    ge, te, le, base = _rendu(en, police)
    ey0, ey1, ex0, ex1 = _encre(ge > seuil)
    k = (y1 - y0 + 1) / float(ey1 - ey0 + 1)             # echelle
    c = (x1 - x0 + 1) / float((ex1 - ex0 + 1) * k)        # chasse
    base_img = y0 + (base - (te + ey0)) * k

    gf, tf, lf, _ = _rendu(fr, police)
    fy0, fy1, fx0, fx1 = _encre(gf > 0.02)
    gf = gf[fy0:fy1 + 1, fx0:fx1 + 1]
    w = gf.shape[1] * k * c
    if largeur_max and w > largeur_max:
        f = largeur_max / w
        if f >= SERRE_MIN:
            c *= f
        else:
            c *= SERRE_MIN
            k *= f / SERRE_MIN
    k *= reduit
    if plafond is not None:
        haut = base_img - (base - (tf + fy0)) * k
        if haut < plafond:
            k *= (base_img - plafond) / float(base_img - haut)
    W = max(1, int(round(gf.shape[1] * k * c)))
    H = max(1, int(round(gf.shape[0] * k)))
    g = np.asarray(Image.fromarray((gf * 255).astype("uint8"))
                   .resize((W, H), Image.LANCZOS), dtype=float) / 255.0
    haut = int(round(base_img - (base - (tf + fy0)) * k))
    return g, haut, x0


def _pose(z, g, y, x, couleur):
    """Melange RVB (fond opaque)."""
    h, w = g.shape
    b = z[y:y + h, x:x + w, :3]
    m = g[..., None]
    b[:] = b * (1 - m) + np.asarray(couleur, float) * m


# --------------------------------------------------------------- elements

def bandeau(a, lignes, cap, mots, police=HATTEN):
    """Le bandeau rouge des commandes.

    `lignes` = (Y0, Y1), la hauteur du bandeau ; `cap` = (y0, y1), l'encre
    des mots anglais ; `mots` = [((debut, fin, icone suivante), en, fr)].
    """
    Y0, Y1 = lignes
    for (x0, x1, icone), en, fr in mots:
        z = a[Y0:Y1, x0 - 4:x1 + 5]
        m = z[..., :3].min(axis=2) > 90                  # blanc, et son bord
        z[..., :3] = rebouche.diffuse(z[..., :3], rebouche.dilate(m, 1), 300)
        g, y, x = comme(en, fr, police, (cap[0], cap[1], x0, x1),
                        largeur_max=icone - 14 - x0)
        _pose(a, g, y, x, (255, 255, 255))
        print("   %-10s -> %-10s %3d px (anglais %3d, place %3d)"
              % (en, fr, g.shape[1], x1 - x0 + 1, icone - 14 - x0))


def _champ(rvb, lettre, en):
    """Le champ de texture : l'original sous ses lettres, ailleurs une copie
    decalee d'une chasse de lettre, puis repete de part et d'autre du mot."""
    ly0, ly1, lx0, lx1 = _encre(lettre)
    champ = rvb.copy()
    fait = lettre.copy()
    pas = (lx1 - lx0 + 1) / float(len(en.replace(" ", "")))
    for n in (1, -1, 2, -2, 0.5, -0.5, 3, -3, 1.5, -1.5, 0.25, -0.25):
        s = int(round(n * pas))
        src = np.zeros_like(lettre)
        if s > 0:
            src[:, :-s] = lettre[:, s:]
        else:
            src[:, -s:] = lettre[:, :s]
        prend = ~fait & src
        ys, xs = np.nonzero(prend)
        champ[ys, xs] = rvb[ys, xs + s]
        fait |= prend
    reste = ~fait
    reste[:, :lx0] = False
    reste[:, lx1 + 1:] = False
    if reste.any():
        champ = rebouche.diffuse(champ, reste, 200)
    for xx in list(range(0, lx0)) + list(range(lx1 + 1, champ.shape[1])):
        champ[:, xx] = champ[:, lx0 + (xx - lx0) % (lx1 - lx0 + 1)]
    return champ


def logo(a, zone, lignes, largeur):
    """Le grand titre grunge, sur une ou plusieurs lignes.

    `zone` = (R0, R1, C0, C1), tout ce qui appartient au logo, halo compris ;
    `lignes` = [(r0, r1, en, fr)], la bande de chaque ligne ; `largeur` : la
    place disponible depuis le debut de l'anglais.
    """
    R0, R1, C0, C1 = zone
    z = a[R0:R1, C0:C1]
    cov = np.zeros(z.shape[:2])
    champ = z[..., :3].copy()
    for r0, r1, en, fr in lignes:
        b = slice(r0 - R0, r1 - R0)
        lettre = z[b, :, 3] >= 250
        ly0, ly1, lx0, lx1 = _encre(lettre)
        g, y, x = comme(en, fr, HATTEN, (r0 + ly0, r0 + ly1, C0 + lx0, C0 + lx1),
                        largeur_max=largeur)
        champ[b] = _champ(z[b, :, :3], lettre, en)
        h, w = g.shape
        c = cov[y - R0:y - R0 + h, x - C0:x - C0 + w]
        c[:] = np.maximum(c, g)
        print("   %-10s -> %-17s %4d x %3d px (anglais %4d x %3d)"
              % (en, fr, w, h, lx1 - lx0 + 1, ly1 - ly0 + 1))

    # on vide la zone, puis lettres + halo
    halo = np.asarray(Image.fromarray((cov * 255).astype("uint8"))
                      .filter(ImageFilter.GaussianBlur(6)), dtype=float) / 255.0
    halo = np.clip(halo * 200.0, 0, 200)
    z[..., 3] = np.maximum(cov * 255.0, halo * (1 - cov))
    plein = cov > 0.02
    z[plein, :3] = champ[plein]
    ombre = ~plein & (halo > 0.5)
    z[ombre, :3] = (8, 2, 5)


def onglet(a, nom):
    en, fr = LOGO[nom]
    Y0, Y1 = 1270, 1312
    z = a[Y0:Y1, ONGLET_X:ONGLET_X + ONGLET_LARGE + 40]
    blanc = (z[..., :3].min(axis=2) > 200) & (z[..., 3] > 200)
    ty0, ty1, tx0, tx1 = _encre(blanc)
    # bord droit de l'aplat : derniere colonne opaque sur la ligne du milieu
    opaque = np.nonzero(z[(Y1 - Y0) // 2, :, 3] > 200)[0]
    droite = opaque.max()
    marge_g, marge_d = tx0, droite - tx1
    g, y, x = comme(en, fr, HATTEN,
                    (Y0 + ty0, Y0 + ty1, ONGLET_X + tx0, ONGLET_X + tx1),
                    largeur_max=ONGLET_LARGE - 1 - marge_g - marge_d)
    # on efface le texte, puis on allonge l'aplat
    m = rebouche.dilate(z[..., :3].min(axis=2) > 120, 1)
    m[:, :3] = False
    z[..., :3] = rebouche.diffuse(z[..., :3], m, 200)
    neuf = tx0 + g.shape[1] + marge_d
    for xx in range(droite + 1, neuf + 1):
        z[:, xx] = z[:, droite - 3]
    _pose(a, g, y, x, (255, 255, 255))
    print("   onglet %-10s -> %-17s %3d px (aplat %d -> %d)"
          % (en, fr, g.shape[1], droite + 1, neuf + 1))


def tampon(a, en, fr, zone):
    """NO DATA, DATA BROKEN : Chiller blanc sur la tache noire.

    Le fond de la tache est d'une couleur parfaitement uniforme ; les lettres
    portent un liseré plus sombre sur 2 ou 3 px, qu'on efface avec elles et
    qu'on redonne aux lettres francaises.
    """
    y0, y1, x0, x1 = zone
    z = a[y0:y1, x0:x1]
    m = (z[..., :3].min(axis=2) > 120) & (z[..., 3] > 60)
    by0, by1, bx0, bx1 = _encre(m)
    centre = x0 + (bx0 + bx1) / 2.0
    zone_m = rebouche.dilate(m, 4)
    solide = (z[..., 3] > 250) & (z[..., :3].max(axis=2) < 90) & ~zone_m
    noir = np.median(z[solide][:, :3], axis=0)
    # l'alpha est diffuse ; au bord de la tache, il ferait un voile gris :
    # on le tire en points de bombe (2 px), a la densite de l'alpha diffuse
    densite = rebouche.diffuse(z[..., 3:4], zone_m, 300)[..., 0] / 255.0
    alea = np.random.RandomState(1).rand((z.shape[0] + 1) // 2, (z.shape[1] + 1) // 2)
    alea = alea.repeat(2, 0).repeat(2, 1)[:z.shape[0], :z.shape[1]]
    bord = zone_m & (densite < 0.97)
    z[bord, 3] = np.where(alea[bord] < densite[bord] ** 2, 255.0, 0.0)
    z[zone_m & ~bord, 3] = 255.0
    z[zone_m, :3] = noir

    g, y, _ = comme(en, fr, CHILLER, (y0 + by0, y0 + by1, x0 + bx0, x0 + bx1),
                    largeur_max=(bx1 - bx0 + 1) * 1.1, seuil=0.5)
    x = int(round(centre - g.shape[1] / 2.0))
    h, w = g.shape
    M = 6
    b = a[y - M:y + h + M, x - M:x + w + M]
    gg = np.zeros(b.shape[:2])
    gg[M:M + h, M:M + w] = g
    lisere = np.asarray(Image.fromarray((gg * 255).astype("uint8"))
                        .filter(ImageFilter.MaxFilter(3))
                        .filter(ImageFilter.GaussianBlur(1.3)), dtype=float) / 255.0
    plein = b[..., 3] > 250
    b[plein, :3] *= (1 - 0.3 * lisere[plein])[:, None]
    b[..., :3] = b[..., :3] * (1 - gg[..., None]) + 255.0 * gg[..., None]
    b[..., 3] = np.maximum(b[..., 3], 255.0 * gg)
    print("   %-11s -> %-10s %3d px (anglais %3d)" % (en, fr, w, bx1 - bx0 + 1))


def etiquette(a, en, fr, zone, largeur_max):
    """SAVETIME, LOCKED : brun, le texte dans l'alpha."""
    y0, y1, x0, x1 = zone
    z = a[y0:y1, x0:x1]
    m = (z[..., 3] > 100) & (z[..., :3].max(axis=2) < 140)
    by0, by1, bx0, bx1 = _encre(m)
    couleur = z[m][:, :3].mean(axis=0)
    plein = z[m][:, 3].max()
    efface = rebouche.dilate(m | ((z[..., 3] > 0) & (z[..., :3].max(axis=2) < 140)), 1)
    z[efface, 3] = 0
    g, y, x = comme(en, fr, HATTEN, (y0 + by0, y0 + by1, x0 + bx0, x0 + bx1),
                    largeur_max=largeur_max)
    h, w = g.shape
    b = a[y:y + h, x:x + w]
    b[..., 3] = np.maximum(b[..., 3], plein * g)
    b[g > 0.02, :3] = couleur
    print("   %-9s -> %-9s %3d px (anglais %3d)" % (en, fr, w, bx1 - bx0 + 1))


def menu(a, nom):
    """loadmenu, savemenu, qloadmenu."""
    en, fr = LOGO[nom]
    # entre le pied des poteaux (1081) et la ligne des PAGE (1388)
    logo(a, (1082, 1386, 0, 1236), [(1082, 1386, en, fr)], LOGO_LARGE)
    onglet(a, nom)
    bandeau(a, (1458, 1506), (1466, 1496), BANDEAU)
    tampon(a, "NO DATA", "VIDE", (10, 165, 1700, 2040))
    tampon(a, "DATA BROKEN", "CORROMPUE", (195, 355, 1695, 2040))
    etiquette(a, "SAVETIME", "DATE", (1418, 1440, 840, 935), 70)
    # LOCKED s'arrete avant le cadenas
    etiquette(a, "LOCKED", "PROTÉGÉ", (1414, 1430, 1330, 1385), 50)
    return a


def backlog(a):
    """Le journal : BACK / LOG sur deux lignes, comme le mot coupe en deux
    sans trait d'union ; HISTO / RIQUE fait pareil. L'icone du haut-parleur,
    a droite de BACK (x 1522), reste hors de la zone."""
    logo(a, (1212, 1760, 965, 1515),
         [(1212, 1479, "BACK", "HISTO"), (1479, 1760, "LOG", "RIQUE")], 490)
    bandeau(a, (1150, 1203), (1162, 1193), [
        ((110, 196, 234), "SELECT", "CHOISIR"),
        ((271, 412, 450), "PLAY VOICE", "ÉCOUTER"),
        ((494, 557, 1100), "BACK", "RETOUR"),
    ])
    return a


def clearlist(a):
    """Les fins atteintes. Les noms des fins (OVER SKY END, REAL SKY END...)
    sont des titres, comme ceux des morceaux : ils restent en anglais."""
    bandeau(a, (2265, 2314), (2274, 2304), [((110, 173, 1100), "BACK", "RETOUR")])
    return a


# ------------------------------------------------------------ bibliotheque

def _transforme(g, theta, k):
    """Inclinaison horizontale k puis rotation theta (degres), sur une
    couverture ; rend la couverture recadree sur son encre."""
    t = np.radians(theta)
    A = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]]).dot(
        np.array([[1.0, k], [0.0, 1.0]]))
    h, w = g.shape
    coins = A.dot(np.array([[0, w, 0, w], [0, 0, h, h]], float))
    ox, oy = coins[0].min(), coins[1].min()
    W = int(np.ceil(coins[0].max() - ox)) + 2
    H = int(np.ceil(coins[1].max() - oy)) + 2
    inv = np.linalg.inv(A)
    # sortie (u, v) -> entree : inv . (u + ox, v + oy)
    c = (inv[0, 0], inv[0, 1], inv[0, 0] * ox + inv[0, 1] * oy,
         inv[1, 0], inv[1, 1], inv[1, 0] * ox + inv[1, 1] * oy)
    im = Image.fromarray((g * 255).astype("uint8")).transform(
        (W, H), Image.AFFINE, c, resample=Image.BICUBIC)
    r = np.asarray(im, dtype=float) / 255.0
    y0, y1, x0, x1 = _encre(r > 0.02)
    return r[y0:y1 + 1, x0:x1 + 1]


def incline(masque, en, fr, police, angle0=None, longueur_max=None,
            direction=None):
    """Le francais avec l'inclinaison et la rotation de l'anglais.

    On cherche la rotation et l'inclinaison qui, appliquees a l'anglais
    rendu, recouvrent le mieux `masque` ; le francais recoit les memes, et
    la meme echelle. Rend la couverture du francais.

    `angle0` : l'angle approximatif de la ligne (on cherche a 6 degres
    autour). `longueur_max` : la place le long de `direction` ; au-dela, le
    francais est resserre.
    """
    y0, y1, x0, x1 = _encre(masque)
    cible = masque[y0:y1 + 1, x0:x1 + 1].astype(float)
    H, W = cible.shape
    ge = _rendu(en, police)[0]
    gf = _rendu(fr, police)[0]
    if angle0 is None:
        angles, incl = np.arange(-30, 10.1, 1.0), np.arange(-0.6, 0.31, 0.05)
    else:
        # une ligne droite d'un texte droit : peu de jeu autour de l'angle
        angles = np.arange(angle0 - 4, angle0 + 4.1, 0.5)
        incl = np.arange(-0.1, 0.11, 0.05)
    meilleur = None
    for theta in angles:
        for k in incl:
            r = _transforme(ge, theta, k)
            rr = np.asarray(Image.fromarray((r * 255).astype("uint8"))
                            .resize((W, H), Image.LANCZOS), dtype=float) / 255.0
            s = np.minimum(rr, cible).sum() / np.maximum(rr, cible).sum()
            if meilleur is None or s > meilleur[0]:
                meilleur = (s, theta, k, r.shape)
    s, theta, k, (he, we) = meilleur
    sx, sy = W / float(we), H / float(he)
    serre = 1.0
    for _ in range(8):
        gs = gf
        if serre < 1.0:
            gs = np.asarray(Image.fromarray((gf * 255).astype("uint8")).resize(
                (max(1, int(gf.shape[1] * serre)), gf.shape[0]), Image.LANCZOS),
                dtype=float) / 255.0
        rf = _transforme(gs, theta, k)
        w = max(1, int(round(rf.shape[1] * sx)))
        h = max(1, int(round(rf.shape[0] * sy)))
        g = np.asarray(Image.fromarray((rf * 255).astype("uint8"))
                       .resize((w, h), Image.LANCZOS), dtype=float) / 255.0
        if longueur_max is None or direction is None:
            break
        gy, gx = np.nonzero(g > 0.3)
        lu = gx * direction[0] + gy * direction[1]
        etendue = lu.max() - lu.min()
        if etendue <= longueur_max:
            break
        serre *= longueur_max / float(etendue)
    print("   %-24s -> %-26s rotation %+.1f, inclinaison %+.2f (recouvrement %.2f%s)"
          % (en, fr, theta, k, s, ", resserre %.2f" % serre if serre < 1 else ""))
    return g


def _lettres(m, tailles, large=60):
    """Les composantes de `m` dont la hauteur est dans `tailles`."""
    lab, infos = composantes.composantes(m)
    garde = np.zeros(m.shape, bool)
    for i, (n, y0, y1, x0, x1) in enumerate(infos, 1):
        if tailles[0] <= y1 - y0 + 1 <= tailles[1] and x1 - x0 + 1 <= large:
            garde |= lab == i
    return garde


def panneau(a, zone, en, fr, clair, tailles, largeur_max=None, incliner=False,
            rectangle=False, police=HATTEN, gauche=False, x_min=0, large=60,
            rouille=True, seuil=150, marge=2):
    """Le texte d'un panneau routier : on rebouche par diffusion (les bandes
    sombres du panneau sont masquees pendant le calcul, pour ne pas deteindre)
    puis on pose le francais, centre sur l'anglais.

    `rectangle` : on rebouche tout le rectangle du mot, et pas seulement les
    lettres, quand une tache de rouille mange le bas des lettres (sinon le
    bas tache des anciennes lettres resterait). `gauche` : cale a gauche au
    lieu de centrer. `x_min` : ce qui est avant (une icone) n'est pas du texte.
    """
    Y0, Y1, X0, X1 = zone
    z = a[Y0:Y1, X0:X1]
    avant = z.copy()
    lum = z[..., :3].mean(axis=2)
    texte = (lum > seuil) if clair else (lum < 110)
    texte &= z[..., 3] > 200
    texte[:, :x_min] = False
    lettres = _lettres(texte, tailles, large)
    # la couleur du coeur des lettres, sans l'anticrenelage : le tiers le
    # plus clair (texte clair) ou le plus sombre (texte sombre)
    px = z[lettres][:, :3]
    l = px.mean(axis=1)
    coeur = l >= np.percentile(l, 67) if clair else l <= np.percentile(l, 33)
    couleur = px[coeur].mean(axis=0)
    if rectangle:
        ly0, ly1, lx0, lx1 = _encre(lettres)
        trou = np.zeros(lettres.shape, bool)
        trou[ly0 - 3:ly1 + 4, lx0 - 3:lx1 + 4] = True
        trou &= z[..., 3] > 250
    else:
        trou = rebouche.dilate(lettres, marge) & (z[..., 3] > 250)
    fond = z[..., :3].copy()
    autre = texte & ~lettres                       # bandes, bord, rouille
    fond[autre] = np.median(z[~texte & (z[..., 3] > 250)][:, :3], axis=0)
    fond = rebouche.diffuse(fond, trou, 400)
    z[trou, :3] = fond[trou]
    ly0, ly1, lx0, lx1 = _encre(lettres)
    if incliner:
        g = incline(lettres, en, fr, police)
        h, w = g.shape
        y = int(round((ly0 + ly1) / 2.0 - h / 2.0))
    else:
        g, y, _ = comme(en, fr, police, (ly0, ly1, lx0, lx1),
                        largeur_max=largeur_max)
        print("   %-11s -> %-10s %3d px (anglais %3d)" % (en, fr, g.shape[1], lx1 - lx0 + 1))
        h, w = g.shape
    x = lx0 if gauche else int(round((lx0 + lx1) / 2.0 - w / 2.0))
    b = z[y:y + h, x:x + w, :3]
    if clair and rouille:
        # la rouille qui tache le fond tache aussi les lettres
        ref = np.median(fond[trou], axis=0).mean()
        tache = np.clip(fond[y:y + h, x:x + w].mean(axis=2) / max(ref, 1), 0.5, 1.0)
        c = couleur[None, None, :] * (tache ** 0.7)[..., None]
    else:
        c = couleur[None, None, :]
    b[:] = b * (1 - g[..., None]) + c * g[..., None]
    # ce qui a la couleur du texte sans en etre (mouchetures, bandes du
    # panneau) revient tel quel, par-dessus
    remet = autre & trou
    z[remet, :3] = avant[remet, :3]


def peinture(a, boite, en, fr):
    """Le titre peint a la bombe (LIBRARY) : lettres pleines, eclaboussures
    et coulures dans la meme encre.

    On efface toute l'encre de la bande des lettres : les eclaboussures et
    les coulures qui en sortent restent, coupees au ras de la bande, et se
    raccordent aux nouvelles lettres, posees dans la meme boite. Les
    mouchetures claires des anciennes lettres sont reportees sur les
    nouvelles, par l'alpha.
    """
    y0, y1, x0, x1 = boite
    z = a[y0:y1 + 1, x0:x1 + 1]
    encre = z[..., 3] > 200
    coeur = ~rebouche.dilate(~encre, 3)
    trame = _champ(z[..., 3:4], coeur, en)[..., 0]
    noir = np.median(z[encre][:, :3], axis=0)

    gf = _rendu(fr, HATTEN)[0]
    fy0, fy1, fx0, fx1 = _encre(gf > 0.5)
    gf = gf[fy0:fy1 + 1, fx0:fx1 + 1]
    W, H = x1 - x0 + 1, y1 - y0 + 1
    chasse = (W / float(H)) / (gf.shape[1] / float(gf.shape[0]))
    g = np.asarray(Image.fromarray((gf * 255).astype("uint8"))
                   .resize((W, H), Image.LANCZOS), dtype=float) / 255.0
    a[y0 - 1:y1 + 2, x0 - 3:x1 + 4, 3] = 0
    z[..., 3] = 255.0 * g * (trame / 255.0)
    z[g > 0.02, :3] = noir
    print("   %-8s -> %-8s %d x %d px, chasse %.2f" % (en, fr, W, H, chasse))


def library(a):
    peinture(a, (35, 266, 31, 800), "LIBRARY", "GALERIE")
    # la rouille mange le bas de MUSIC : M et U sortent tronques
    panneau(a, (565, 625, 1765, 1900), "MUSIC", "MUSIQUE", True, (15, 45),
            largeur_max=102, rectangle=True)
    # 24 px au moins : un bout de bande du panneau en fait 21
    panneau(a, (795, 865, 1840, 1945), "MOVIE", "FILMS", False, (24, 45),
            incliner=True)
    bandeau(a, (1783, 1832), (1792, 1822), [
        ((110, 196, 234), "SELECT", "CHOISIR"),
        ((271, 386, 423), "CONFIRM", "VALIDER"),
        ((486, 654, 691), "CHANGE PAGE", "CHANGER DE PAGE"),
        ((735, 798, 1100), "BACK", "RETOUR"),
    ])
    bandeau(a, (1881, 1930), (1890, 1920), [
        ((110, 196, 234), "SELECT", "CHOISIR"),
        ((271, 374, 412), "NEXT CG", "SUIVANTE"),
        ((464, 648, 685), "DISABLE GUIDE", "MASQUER L\u2019AIDE"),
        ((902, 965, 1100), "BACK", "RETOUR"),
    ])
    bandeau(a, (1880, 1930), (1898, 1916),
            [((1640, 1736, 1807), "VARIATION", "VARIANTE")], police=FRANKLIN)
    return a


# ------------------------------------------------------------------ musique

ARIAL_BLACK = "C:/Windows/Fonts/ariblk.ttf"


def dans_alpha(a, boite, en, fr, largeur_max, police=HATTEN, reduit=1.0):
    """Un libelle pose sur fond transparent, le texte dans l'alpha et une
    couleur unie. `boite` = l'encre de l'anglais (sans son icone). Les
    accents ne depassent pas le haut de l'anglais."""
    y0, y1, x0, x1 = boite
    z = a[y0 - 2:y1 + 3, x0 - 2:x1 + 3]
    plein = z[..., 3] > 250
    couleur = np.median(z[plein][:, :3], axis=0)
    z[..., 3] = 0
    g, y, x = comme(en, fr, police, boite, largeur_max=largeur_max, reduit=reduit)
    h, w = g.shape
    b = a[y:y + h, x:x + w]
    b[..., 3] = np.maximum(b[..., 3], 255.0 * g)
    b[g > 0.02, :3] = couleur
    print("   %-11s -> %-13s %3d px (anglais %3d)" % (en, fr, w, x1 - x0 + 1))


def music(a):
    bandeau(a, (1293, 1342), (1301, 1332), [
        ((110, 196, 234), "SELECT", "CHOISIR"),
        ((271, 329, 367), "PLAY", "LIRE"),
        ((419, 480, 518), "STOP", "ARR\u00caT"),
        ((570, 820, 857), "CHANGE PLAY MODE", "MODE DE LECTURE"),
        ((901, 964, 1300), "BACK", "RETOUR"),
    ])
    # les modes de lecture : petits sprites, a 20 px de l'anglais au plus.
    # Les accents ne depassent pas le haut des icones (1309) : on calcule la
    # reduction qu'il faut au mot le plus contraint et on l'applique aux
    # quatre, pour qu'ils restent de la meme taille.
    modes = [((2014, 2137), "PLAY ALL", "TOUT LIRE"),
             ((2248, 2360), "SHUFFLE", "AL\u00c9ATOIRE"),
             ((2474, 2629), "REPEAT ALL", "R\u00c9P\u00c9TER TOUT"),
             ((2746, 2907), "REPEAT ONE", "R\u00c9P\u00c9TER UN")]
    reduit = 1.0
    for (x0, x1), en, fr in modes:
        b = (1311, 1339, x0, x1)
        h0 = comme(en, fr, HATTEN, b, largeur_max=x1 - x0 + 21)[0].shape[0]
        h1 = comme(en, fr, HATTEN, b, largeur_max=x1 - x0 + 21, plafond=1309)[0].shape[0]
        reduit = min(reduit, h1 / float(h0))
    for (x0, x1), en, fr in modes:
        dans_alpha(a, (1311, 1339, x0, x1), en, fr, x1 - x0 + 21, reduit=reduit)
    # sur la bande de papier, qui s'arrete a x 419 ; l'icone finit vers 66
    # les mouchetures soudent les lettres en blocs : on efface le rectangle
    panneau(a, (1365, 1432, 0, 419), "NOW PLAYING", "EN LECTURE", False, (22, 50),
            largeur_max=419 - 8 - 75, police=ARIAL_BLACK, gauche=True, x_min=70,
            large=400, rectangle=True)
    return a
