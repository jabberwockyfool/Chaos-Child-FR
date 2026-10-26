# -*- coding: utf-8 -*-
"""Les panneaux des decors (bg02xx a bg06xx) : enseignes, affiches,
banderoles, plaques, que le Committee of Zero a redessines en anglais par-
dessus le japonais.

Chaque ligne de texte est traitee ainsi :

1. l'encre de l'anglais est isolee dans sa zone (plus sombre, plus claire ou
   d'une couleur donnee que le support autour) ;
2. l'anglais est rendu dans la police choisie et **cale sur cette encre** :
   echelle, rotation, inclinaison et fuite (une perspective le long de la
   ligne), par recouvrement maximal ;
3. l'encre est effacee (diffusion du pourtour, ou recopie du meilleur
   morceau voisin sur un support a motif) ;
4. le francais est rendu dans la meme police et pose avec la meme
   geometrie, centre sur l'anglais, dans la couleur de l'encre d'origine,
   modulee par le grain du support.

Les variantes d'un meme decor (jour, soir, nuit...) recoivent la meme
retouche : la difference entre avant et apres sur l'image de base est
reportee sur la variante a travers la correspondance de couleurs relevee
autour du panneau (une transformation affine des RVB).

    python cg/outils/decors.py [bg0201] [--install]
"""
import io
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RACINE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RACINE)
import rebouche  # noqa: E402

G = 160                  # corps de travail des rendus
POSES = {}               # les poses calees sur l'image de base, par panneau
JP = None                # l'original japonais de l'image en cours (voir main)


# ------------------------------------------------------------ rendu
def rendu(texte, police, graisse=0):
    """Le texte au corps G. Rend (couverture, origine (u, v) de la ligne de
    base dans la couverture, chasse, hauteur des capitales)."""
    ft = ImageFont.truetype(police, G)
    L = int(G * (len(texte) * 1.3 + 3))
    im = Image.new("L", (L, 4 * G), 0)
    ImageDraw.Draw(im).text((G, 2 * G), texte, 255, font=ft, anchor="ls",
                            stroke_width=graisse, stroke_fill=255)
    x0, y0, x1, y1 = im.getbbox()
    g = np.asarray(im.crop((x0 - 2, y0 - 2, x1 + 2, y1 + 2)), dtype=float) / 255.0
    h = ft.getbbox("H", anchor="ls")
    return g, (G - (x0 - 2), 2 * G - (y0 - 2)), ft.getlength(texte), float(h[3] - h[1])


# ------------------------------------------------------------ geometrie
class Pose(object):
    """Une ligne de texte dans l'image : centre (cx, cy), rotation (degres),
    echelles sx, sy, inclinaison k et fuite p (perspective le long de la
    ligne : l'echelle varie de p par unite de longueur rapportee a la
    chasse)."""

    def __init__(self, cx, cy, theta, sx, sy, k=0.0, p=0.0):
        self.cx, self.cy, self.theta, self.sx, self.sy, self.k, self.p = \
            cx, cy, theta, sx, sy, k, p

    def vecteur(self):
        return [self.cx, self.cy, self.theta, self.sx, self.sy, self.k, self.p]

    def matrice(self):
        t = np.radians(self.theta)
        R = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
        return R.dot(np.array([[self.sx, self.k * self.sy], [0.0, self.sy]]))


def pose_texte(g, origine, centre_txt, pose, forme, decalage=(0, 0)):
    """Projette la couverture g dans un canevas `forme` (h, w) dont le coin
    est en `decalage` dans l'image. `centre_txt` : le point du texte (u, v,
    relatif a l'origine) qui va au centre de la pose."""
    h, w = forme
    ys, xs = np.mgrid[0:h, 0:w].astype(float)
    dx = xs + decalage[1] - pose.cx
    dy = ys + decalage[0] - pose.cy
    A = pose.matrice()
    L = max(g.shape[1], 1) / 2.0
    # d = A q / (1 + p qu / L)  =>  (A - d [p / L, 0]) q = d
    a = A[0, 0] - dx * pose.p / L
    b = A[0, 1]
    c = A[1, 0] - dy * pose.p / L
    d = A[1, 1]
    det = a * d - b * c
    det[np.abs(det) < 1e-9] = 1e-9
    qu = (d * dx - b * dy) / det
    qv = (-c * dx + a * dy) / det
    u = qu + centre_txt[0] + origine[0]
    v = qv + centre_txt[1] + origine[1]
    return _echantillonne(g, u, v)


def _echantillonne(g, u, v):
    H, W = g.shape
    u0 = np.floor(u).astype(int)
    v0 = np.floor(v).astype(int)
    fu, fv = u - u0, v - v0
    out = np.zeros(u.shape)
    for du, dv, wgt in ((0, 0, (1 - fu) * (1 - fv)), (1, 0, fu * (1 - fv)),
                        (0, 1, (1 - fu) * fv), (1, 1, fu * fv)):
        uu, vv = u0 + du, v0 + dv
        ok = (uu >= 0) & (uu < W) & (vv >= 0) & (vv < H)
        val = np.zeros(u.shape)
        val[ok] = g[vv[ok], uu[ok]]
        out += wgt * val
    return out


def _rendu_reduit(texte, police, echelle, graisse=0):
    """Le rendu au corps G, puis reduit pres de l'echelle d'arrivee : la
    projection echantillonne alors sans crenelage."""
    g, (ou, ov), chasse, cap = rendu(texte, police, graisse)
    f = min(1.0, max(echelle, 0.02) * 1.5)
    if f < 1.0:
        W, H = max(1, int(round(g.shape[1] * f))), max(1, int(round(g.shape[0] * f)))
        g = np.asarray(Image.fromarray((g * 255).astype("uint8")).resize((W, H), Image.LANCZOS),
                       dtype=float) / 255.0
    return g, (ou * f, ov * f), chasse * f, cap * f, f


# ------------------------------------------------------------ calage
def cale(masque, texte, police, graisse=0, theta0=None, fuite=False, iterations=4,
         incliner=True):
    """La pose qui recouvre le mieux `masque` (couverture 0..1 de la zone)
    avec `texte` rendu dans `police`. Rend (recouvrement, pose)."""
    ys, xs = np.nonzero(masque > 0.5)
    cy, cx = ys.mean(), xs.mean()
    if theta0 is None:
        c = np.cov(np.vstack([xs - cx, ys - cy]))
        vp, vec = np.linalg.eigh(c)
        theta0 = np.degrees(np.arctan2(vec[1, 1], vec[0, 1]))
        if theta0 > 90:
            theta0 -= 180
        if theta0 < -90:
            theta0 += 180
    t = np.radians(theta0)
    along = (xs - cx) * np.cos(t) + (ys - cy) * np.sin(t)
    g, ori, chasse, cap = rendu(texte, police, graisse)
    gy, gx = np.nonzero(g > 0.5)
    s0 = (along.max() - along.min()) / float(gx.max() - gx.min() + 1)
    centre = centre_encre(texte, police, graisse)[0]
    gr, orir, _, _, f = _rendu_reduit(texte, police, s0, graisse)
    centre_r = (centre[0] * f, centre[1] * f)
    pose = Pose(cx, cy, theta0, s0 / f, s0 / f)
    cible = masque.astype(float)

    def score(v):
        P = Pose(*v)
        r = pose_texte(gr, orir, centre_r, P, cible.shape)
        return np.minimum(r, cible).sum() / max(np.maximum(r, cible).sum(), 1e-6)

    v = pose.vecteur()
    meilleur = score(v)
    pas = [2.0, 2.0, 1.0, 0.03 * v[3], 0.03 * v[4], 0.04, 0.03]
    actifs = [0, 1, 2, 3, 4] + ([5] if incliner else []) + ([6] if fuite else [])
    for _ in range(iterations):
        for i in actifs:
            for _ in range(6):
                bouge = False
                for s in (1, -1):
                    w = list(v)
                    w[i] += s * pas[i]
                    sc = score(w)
                    if sc > meilleur:
                        meilleur, v, bouge = sc, w, True
                        break
                if not bouge:
                    break
        pas = [p / 2.0 for p in pas]
    P = Pose(*v)
    P.sx *= f
    P.sy *= f
    return meilleur, P, centre


def choisit_police(masque, texte, polices, graisse=0, theta0=None):
    res = []
    for p in polices:
        try:
            s, P, c = cale(masque, texte, p, graisse, theta0, iterations=2)
        except Exception:
            continue
        res.append((s, p))
    return sorted(res, reverse=True)


# ------------------------------------------------------------ encre
def encre(z, mode, seuil=40, couleur=None, rayon=6):
    """Couverture 0..1 de l'encre de la zone z (RVB float)."""
    lum = z.mean(axis=2)
    if mode == "sombre":
        fond = np.asarray(Image.fromarray(np.clip(lum, 0, 255).astype("uint8"))
                          .filter(ImageFilter.MaxFilter(2 * rayon + 1)), dtype=float)
        return np.clip((fond - lum - seuil * 0.5) / (seuil * 0.5), 0, 1)
    if mode == "clair":
        fond = np.asarray(Image.fromarray(np.clip(lum, 0, 255).astype("uint8"))
                          .filter(ImageFilter.MinFilter(2 * rayon + 1)), dtype=float)
        return np.clip((lum - fond - seuil * 0.5) / (seuil * 0.5), 0, 1)
    if mode == "couleur":
        d = np.sqrt(((z - np.array(couleur, float)) ** 2).sum(axis=2))
        return np.clip((seuil * 1.5 - d) / (seuil * 0.5), 0, 1)
    raise ValueError(mode)


# ------------------------------------------------------------ couleur
def transfere(base_avant, base_apres, variante, zone, marge=12, bins=32):
    """Reporte sur `variante` la retouche faite sur la base dans `zone`.

    La correspondance des couleurs entre base et variante est relevee
    autour du panneau, canal par canal : pour chaque niveau de la base, la
    mediane de la variante (une courbe, qui suit aussi les saturations d'un
    eclairage force). La variante recoit courbe(apres) - courbe(avant) : son
    grain propre est garde."""
    y0, y1, x0, x1 = zone
    Y0, Y1 = max(0, y0 - marge), min(base_avant.shape[0], y1 + marge)
    X0, X1 = max(0, x0 - marge), min(base_avant.shape[1], x1 + marge)
    ecart = 0.0
    av = base_avant[y0:y1, x0:x1, :3]
    ap = base_apres[y0:y1, x0:x1, :3]
    for c in range(3):
        b = base_avant[Y0:Y1, X0:X1, c].ravel()
        v = variante[Y0:Y1, X0:X1, c].ravel()
        bords = np.linspace(0, 256, bins + 1)
        xs, ys = [], []
        for k in range(bins):
            sel = (b >= bords[k]) & (b < bords[k + 1])
            if sel.sum() >= 8:
                xs.append(np.median(b[sel]))
                ys.append(np.median(v[sel]))
        xs, ys = np.array(xs), np.array(ys)
        ys = np.maximum.accumulate(ys)          # monotone
        courbe = lambda t: np.interp(t, xs, ys)
        ecart += np.sqrt(((courbe(b) - v) ** 2).mean()) / 3.0
        variante[y0:y1, x0:x1, c] = np.clip(
            variante[y0:y1, x0:x1, c] + courbe(ap[..., c]) - courbe(av[..., c]), 0, 255)
    return ecart


# ------------------------------------------------------------ panneau
def couverture_ligne(texte, police, pose, centre, forme, decalage=(0, 0), graisse=0,
                     serre=1.0):
    """Le texte pose dans un canevas (h, w) ; `serre` resserre la chasse."""
    g, ori, chasse, cap, f = _rendu_reduit(texte, police, pose.sx, graisse)
    if serre != 1.0:
        W = max(1, int(round(g.shape[1] * serre)))
        g = np.asarray(Image.fromarray((g * 255).astype("uint8")).resize((W, g.shape[0]), Image.LANCZOS),
                       dtype=float) / 255.0
        ori = (ori[0] * serre, ori[1])
    # g est au corps G x f (et resserre en largeur) : l'echelle de la pose
    # s'entend au corps G
    P = Pose(pose.cx, pose.cy, pose.theta, pose.sx / f, pose.sy / f, pose.k, pose.p)
    return pose_texte(g, ori, (centre[0] * f * serre, centre[1] * f), P, forme, decalage)


def centre_encre(texte, police, graisse=0):
    """Le point d'ancrage d'une ligne (milieu de l'encre en largeur, mi-
    hauteur des capitales au-dessus de la ligne de base), le debut de son
    encre et sa largeur, relatifs a l'origine."""
    g, ori, chasse, cap = rendu(texte, police, graisse)
    gy, gx = np.nonzero(g > 0.5)
    return ((gx.min() + gx.max()) / 2.0 - ori[0], -cap / 2.0), gx.min() - ori[0],         (gx.max() - gx.min() + 1)


def retouche(y0, y1, x0, x1, z, m, seuil=6):
    """L'encre m, restreinte a ce que le Committee of Zero a peint dans la
    zone : ce qui differe de l'original japonais. Le texte anglais est de
    leur main ; ce qui est reste identique (un bord, un cadre, le dessin)
    n'en est pas. Quand l'anglais est d'origine (le japonais l'avait deja),
    l'encre est rendue telle quelle. Rend (encre, intact) : `intact`, ce
    qui n'a pas a etre efface."""
    rien = np.zeros(m.shape, bool)
    if JP is None or JP.shape[0] < y1 or JP.shape[1] < x1:
        return m, rien
    r = np.abs(z - JP[y0:y1, x0:x1, :3]).max(axis=2) > seuil
    # la ou l'anglais recouvre l'encre japonaise, les deux sont sombres : on
    # ferme les petits manques
    r = ~rebouche.dilate(~rebouche.dilate(r, 2), 2)
    if ((m > 0.5) & r).sum() < 0.3 * max((m > 0.5).sum(), 1):
        return m, rien
    return m * r, ~r


def sombre(seuil=40, rayon=6):
    return lambda zz: encre(zz, "sombre", seuil, rayon=rayon)


def clair(seuil=40, rayon=6):
    return lambda zz: encre(zz, "clair", seuil, rayon=rayon)


def teinte(couleur, seuil=40):
    return lambda zz: encre(zz, "couleur", seuil, couleur)


def bleu(seuil=40):
    """Une encre bleue sur un support neutre."""
    return lambda zz: np.clip(((zz[..., 2] - zz[..., 0]) - seuil) / (seuil * 0.75), 0, 1)


def rouge(seuil=40):
    return lambda zz: np.clip(((zz[..., 0] - zz[..., 2]) - seuil) / (seuil * 0.75), 0, 1)


def plus_rouge(ecart=20):
    """Plus rouge que la teinte ambiante de la zone (un eclairage du soir
    rougit tout)."""
    def f(zz):
        # rouge contre vert : le gris (lettres, papier) a r - v a peu pres
        # constant sous tous les eclairages, l'encre rouge non
        d = zz[..., 0] - zz[..., 1]
        return np.clip((d - np.median(d) - ecart) / (ecart * 0.75), 0, 1)
    return f


def tailles(f, hmin, hmax, wmax=None):
    """Ne garde de l'encre de f que les composantes de hauteur hmin..hmax
    (et de largeur au plus wmax) : les lettres, sans les filets ni les
    reflets."""
    import composantes

    def g(zz):
        m = f(zz)
        lab, cs = composantes.composantes(m > 0.4)
        garde = np.zeros(m.shape, bool)
        for i, (n, y0, y1, x0, x1) in enumerate(cs):
            h, w = y1 - y0 + 1, x1 - x0 + 1
            if hmin <= h <= hmax and (wmax is None or w <= wmax):
                garde |= lab == i + 1
        return m * rebouche.dilate(garde, 2)
    return g


def sature(seuil=35):
    """Ce qui est colore (le decor autour d'un panneau blanc a lettres
    grises) : a proteger."""
    return lambda zz: (zz.max(axis=2) - zz.min(axis=2)) > seuil


def union(*fs):
    return lambda zz: np.maximum.reduce([f(zz) for f in fs])


def _flou_max(g, r):
    if r <= 0:
        return g
    im = Image.fromarray((g * 255).astype("uint8")).filter(ImageFilter.MaxFilter(2 * r + 1))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(0.6)), dtype=float) / 255.0


def _flou_min(g, r):
    if r <= 0:
        return g
    im = Image.fromarray((g * 255).astype("uint8")).filter(ImageFilter.MinFilter(2 * r + 1))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(0.6)), dtype=float) / 255.0


def regraine(z, trou, avant, rayon=2.0, graine=0):
    """Rend au trou rebouche (lisse) le grain du support : le residu fin
    (image moins son flou) de pixels sains tires au hasard dans la zone."""
    flou = np.stack([np.asarray(Image.fromarray(np.clip(avant[..., c], 0, 255).astype("uint8"))
                                .filter(ImageFilter.GaussianBlur(rayon)), dtype=float)
                     for c in range(3)], axis=2)
    residu = np.clip(avant - flou, -12, 12)
    # le grain du support seul : des pixels sains de la meme teinte que le
    # trou rebouche (ni le decor voisin, ni les bords)
    cible = np.median(z[trou], axis=0)
    proche = np.sqrt(((flou - cible) ** 2).sum(axis=2)) < 20
    sains = ~rebouche.dilate(trou, 3) & proche
    ys, xs = np.nonzero(sains)
    if len(ys) == 0 or not trou.any():
        return z
    r = np.random.RandomState(graine)
    k = r.randint(0, len(ys), trou.sum())
    z[trou] = np.clip(z[trou] + residu[ys[k], xs[k]], 0, 255)
    return z


def _decale(g, dx, dy):
    """g translate de (dx, dy) pixels (entiers ou non)."""
    im = Image.fromarray((g * 255).astype("uint8"))
    r = im.transform(im.size, Image.AFFINE, (1, 0, -dx, 0, 1, -dy), resample=Image.BILINEAR)
    return np.asarray(r, dtype=float) / 255.0


def _bords(masque, x0, x1, degre=2):
    """Les lignes du haut et du bas d'un texte en capitales, en fonction de
    x : polynomes ajustes sur le haut et le bas de l'encre, colonne par
    colonne (les colonnes vides entre les lettres sont ignorees)."""
    xs, hauts, bas = [], [], []
    for x in range(x0, x1 + 1):
        ys = np.nonzero(masque[:, x] > 0.5)[0]
        if len(ys) >= 3:
            xs.append(x)
            hauts.append(ys.min())
            bas.append(ys.max())
    xs, hauts, bas = np.array(xs), np.array(hauts), np.array(bas)
    # les colonnes de traits horizontaux (barre du A, du H) mentent : on
    # garde le haut le plus haut et le bas le plus bas par fenetre
    ph = np.polyfit(xs, hauts, degre)
    pb = np.polyfit(xs, bas, degre)
    for _ in range(3):
        r = hauts - np.polyval(ph, xs)
        ok = r <= np.percentile(r, 60)
        ph = np.polyfit(xs[ok], hauts[ok], degre)
        r = bas - np.polyval(pb, xs)
        ok = r >= np.percentile(r, 40)
        pb = np.polyfit(xs[ok], bas[ok], degre)
    return ph, pb


def ruban(forme, texte, police, ph, pb, x0, x1, graisse=0):
    """Le texte plaque entre les courbes ph (haut des capitales) et pb
    (ligne de base), de x0 a x1."""
    g, ori, chasse, cap = rendu(texte, police, graisse)
    gy, gx = np.nonzero(g > 0.5)
    u0, u1 = gx.min(), gx.max()
    v_haut, v_base = ori[1] - cap, ori[1]
    h, w = forme
    ys, xs = np.mgrid[0:h, 0:w].astype(float)
    haut = np.polyval(ph, xs)
    bas = np.polyval(pb, xs)
    u = u0 + (xs - x0) / float(x1 - x0) * (u1 - u0)
    v = v_haut + (ys - haut) / np.maximum(bas - haut, 1.0) * (v_base - v_haut)
    # la couverture est echantillonnee bien plus fine que l'arrivee : on la
    # reduit d'abord a l'echelle (sinon crenelage)
    f = max(1.0, (v_base - v_haut) / max(np.median(bas - haut), 1.0))
    if f > 1.5:
        k = 1.0 / (f / 1.5)
        W, H = max(1, int(g.shape[1] * k)), max(1, int(g.shape[0] * k))
        g = np.asarray(Image.fromarray((g * 255).astype("uint8")).resize((W, H), Image.LANCZOS),
                       dtype=float) / 255.0
        u, v = u * k, v * k
    out = _echantillonne(g, u, v)
    out[(xs < x0 - 2) | (xs > x1 + 2)] = 0
    return out


def _tourne(m, angle, centre):
    """m tourne de `angle` degres (positif : sens horaire a l'ecran, le
    texte descend vers la droite) autour de `centre` (x, y)."""
    im = Image.fromarray((np.clip(m, 0, 1) * 255).astype("uint8"))
    return np.asarray(im.rotate(-angle, resample=Image.BICUBIC, center=centre),
                      dtype=float) / 255.0


def _tourne_f(z, angle, centre, fond=None):
    """Un tableau (h, w, 3) flottant tourne de `angle` degres (sens horaire
    a l'ecran) autour de centre (x, y). Les coins decouverts prennent `fond`
    (par defaut, la mediane du canal)."""
    out = np.zeros_like(z)
    for c in range(z.shape[2]):
        im = Image.fromarray(z[..., c].astype(np.float32), mode="F")
        f = float(np.median(z[..., c])) if fond is None else float(fond)
        out[..., c] = np.asarray(im.rotate(-angle, resample=Image.BICUBIC, center=centre,
                                           fillcolor=f))
    return out


def redresse(a, zone, angle, retouche_):
    """Retouche un panneau penche de `angle` degres (positif : le texte
    descend vers la droite). La zone est redressee, `retouche_` la traite a
    l'horizontale (coordonnees dans la zone redressee), puis seule la
    difference est tournee en sens inverse et ajoutee a l'image : ce qui n'a
    pas ete touche reste au pixel pres."""
    global JP
    y0, y1, x0, x1 = zone
    z = a[y0:y1, x0:x1, :3].copy()
    centre = ((x1 - x0) / 2.0, (y1 - y0) / 2.0)
    droit = _tourne_f(z, -angle, centre)
    jp = JP
    if JP is not None:
        JP = _tourne_f(JP[y0:y1, x0:x1, :3], -angle, centre)
    try:
        apres = retouche_(droit.copy())
    finally:
        JP = jp
    retour = _tourne_f(apres, angle, centre)
    # ce qui a change prend le resultat retourne ; le reste garde l'image
    # d'origine (une double rotation l'adoucirait), fondu sur un pixel
    change = (np.abs(apres - droit).max(axis=2) > 0.5).astype(float)
    change = rebouche.dilate(change > 0, 1).astype(float)
    w = _tourne_f(change[..., None].repeat(3, axis=2), angle, centre, fond=0)[..., :1]
    w = np.clip(w * 1.5, 0, 1)
    a[y0:y1, x0:x1, :3] = np.clip(z * (1 - w) + retour * w, 0, 255)
    return a


def _droit(masque, en, fr, police, place, gauche, boite=None, angle=0.0, graisse=0,
           serre_min=None):
    """Le francais a l'echelle de l'anglais mesure a sa boite d'encre, centre
    sur lui (ou cale a gauche) ; rend la couverture dans le canevas.
    `boite` : la boite d'encre (y0, y1, x0, x1) relevee a la main, dans le
    repere du canevas. `angle` : l'inclinaison de la ligne ; l'encre est
    redressee pour la mesure, le francais tourne ensuite d'autant."""
    import habillage
    centre = None
    if angle:
        ys, xs = np.nonzero(masque > 0.5)
        centre = ((xs.min() + xs.max()) / 2.0, (ys.min() + ys.max()) / 2.0)
        masque = _tourne(masque, -angle, centre)
    if boite is None:
        ys, xs = np.nonzero(masque > 0.5)
        boite = (ys.min(), ys.max(), xs.min(), xs.max())
    ys = np.array([boite[0], boite[1]])
    xs = np.array([boite[2], boite[3]])
    largeur = None if place is None else (xs.max() - xs.min() + 1) * place
    if graisse:
        ancien = habillage._rendu

        def gras(texte, pol):
            G = habillage.G
            ft = ImageFont.truetype(pol, G)
            im = Image.new("L", (int(G * (len(texte) + 2)), G * 3), 0)
            ImageDraw.Draw(im).text((G, G), texte, 255, font=ft, stroke_width=graisse,
                                    stroke_fill=255)
            x0, y0, x1, y1 = im.getbbox()
            base = G + ft.getbbox("H")[3]
            return np.asarray(im.crop((x0, y0, x1, y1)), dtype=float) / 255.0, y0, x0, base
        habillage._rendu = gras
    serre_avant = habillage.SERRE_MIN
    if serre_min is not None:
        habillage.SERRE_MIN = serre_min
    try:
        g, y, x = habillage.comme(en, fr, police, (boite[0], boite[1], boite[2], boite[3]),
                                  largeur_max=largeur)
    finally:
        habillage.SERRE_MIN = serre_avant
        if graisse:
            habillage._rendu = ancien
    h, w = g.shape
    if not gauche:
        x = int(round((xs.min() + xs.max()) / 2.0 - w / 2.0))
    out = np.zeros(masque.shape)
    yy0, xx0 = max(0, y), max(0, x)
    yy1, xx1 = min(masque.shape[0], y + h), min(masque.shape[1], x + w)
    out[yy0:yy1, xx0:xx1] = g[yy0 - y:yy1 - y, xx0 - x:xx1 - x]
    if angle:
        out = _tourne(out, angle, centre)
    return out


def panneau(a, lignes, police, masque=None, marge=2, graisse=0, place=None, grain=0.0,
            couleur=None, contour=None, fuite=False, serre_min=0.8, decale=None,
            poses=None, effacer=True, gauche=False, protege=None, theta0=None,
            cle=None, incliner=True, rectangle=False, droit=False, relief=None,
            halo=None, couleurs=None, encres=None, texture=False, angle=0.0,
            tout_coz=False, verbeux=True):
    """Remplace les lignes [(zone (y0, y1, x0, x1), anglais, francais)] d'un
    meme panneau.

    `masque` : la fonction qui isole l'encre d'une zone (couverture 0..1).
    `place` : la largeur permise au francais, en proportion de l'anglais ;
    au-dela on resserre (jusqu'a serre_min), puis on reduit.
    `grain` : combien le grain du support passe dans l'encre (0 a 1).
    `contour` : (couleur, epaisseur en pixels) d'un lisere trace autour des
    lettres (au-dehors) ; la couleur `couleur` est alors celle du
    remplissage. ("auto", e) : le lisere a la couleur de l'encre relevee, le
    remplissage est a mi-chemin du support.
    `decale` : deplacements (dy, dx) de chaque ligne francaise.
    `gauche` : cale le francais sur le debut de l'anglais (un panneau coupe
    par le bord de l'image).
    `protege` : la fonction qui marque ce qui passe devant le panneau (un
    ballon) : rien n'y est efface ni peint.
    `relief` : (couleur, dx, dy, epaisseur) des lettres en volume : le flanc
    est la face decalee pas a pas de (dx, dy), peint sous elle.
    `encres` : en mode droit, la boite d'encre de chaque anglais (y0, y1,
    x0, x1, dans l'image), relevee a la main.
    `angle` : en mode droit, l'inclinaison de la ligne (degres, positif si
    le texte descend vers la droite).
    `tout_coz` : efface tout ce que le CoZ a repeint dans les zones (un
    support uni, une encre peu contrastee).
    `texture` : rend le grain du support au trou rebouche.
    `couleurs` : une couleur par ligne (sinon `couleur`, relevee).
    `halo` : (rayon, force) d'une lueur claire autour des lettres.
    `droit` : texte horizontal trop petit pour un calage : l'anglais est
    mesure a sa boite d'encre (habillage.comme) et le francais centre dessus.
    `rectangle` : efface toute la zone de chaque ligne, et pas seulement
    l'encre (des lettres dont le remplissage a la couleur du support).
    `poses` : les poses deja calees (sur l'image de base d'une serie de
    variantes) ; rendues pour la suite."""
    if masque is None:
        masque = sombre()
    polices = police if isinstance(police, (list, tuple)) else [police] * len(lignes)
    if cle is not None and poses is None:
        poses = POSES.get(cle)
    Y0 = min(l[0][0] for l in lignes)
    Y1 = max(l[0][1] for l in lignes)
    X0 = min(l[0][2] for l in lignes)
    X1 = max(l[0][3] for l in lignes)
    M = 6
    Y0, X0 = max(0, Y0 - M), max(0, X0 - M)
    Y1, X1 = min(a.shape[0], Y1 + M), min(a.shape[1], X1 + M)
    z = a[Y0:Y1, X0:X1, :3]
    calees, masques = [], []
    trou = np.zeros(z.shape[:2], bool)
    intact = np.zeros(z.shape[:2], bool)
    for i, ((y0, y1, x0, x1), en, fr) in enumerate(lignes):
        zz = z[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0]
        m, ok = retouche(y0, y1, x0, x1, zz, masque(zz))
        intact[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] |= ok
        if tout_coz and ok.any():
            trou[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] |= rebouche.dilate(~ok, 1)
        if droit:
            s, P = 0.0, Pose(0, 0, 0, 1, 1)
        elif poses is None:
            s, P, c = cale(m, en, polices[i], graisse, theta0=theta0, fuite=fuite,
                           incliner=incliner)
            if contour is not None:
                # l'encre relevee est la lettre avec son lisere : on recale
                # avec le lisere
                k = int(round(contour[1] / max(P.sx, 1e-3)))
                s, P, c = cale(m, en, polices[i], graisse + k, theta0=P.theta, fuite=fuite,
                               incliner=incliner)
            P.cx += x0 - X0
            P.cy += y0 - Y0
        else:
            s, P = poses[i]
        calees.append((s, P))
        mm = np.zeros(z.shape[:2])
        mm[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = m
        masques.append(mm)
        if droit:
            calees[-1] = (0.0, P)
        if rectangle:
            trou[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = True
        else:
            trou |= rebouche.dilate(mm > 0.2, marge)
    tout = np.maximum.reduce(masques)
    devant = (np.asarray(protege(z)) > 0.5) if protege is not None else np.zeros(z.shape[:2], bool)
    trou &= ~devant & ~intact
    if couleur is None:
        # le coeur des traits : le tiers le plus marque de l'encre
        px = z[tout > 0.5]
        l = px.mean(axis=1)
        fonce = np.median(z[~trou].mean(axis=1)) > l.mean()
        coeur = l <= np.percentile(l, 33) if fonce else l >= np.percentile(l, 67)
        couleur = np.median(px[coeur], axis=0)
    couleur = np.asarray(couleur, float)
    avant = z.copy()
    if effacer and rectangle:
        # toute trace de trait dans le rectangle, meme pale, et on diffuse
        # depuis le support qui reste entre les traits
        trou = np.zeros(z.shape[:2], bool)
        for i, ((y0, y1, x0, x1), en, fr) in enumerate(lignes):
            r = np.zeros(z.shape[:2], bool)
            r[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = True
            trou |= r & rebouche.dilate(masques[i] > 0.08, 2)
        trou &= ~devant & ~intact
        z[:] = rebouche.diffuse(z, trou, 500)
    elif effacer:
        if devant.any():
            # ce qui passe devant ne doit pas deteindre dans le trou : on le
            # remplace, le temps de la diffusion, par la teinte du support
            tmp = z.copy()
            support = ~trou & ~devant & ~(tout > 0.2)
            if support.any():
                tmp[devant] = np.median(z[support], axis=0)
            z[trou] = rebouche.diffuse(tmp, trou, 500)[trou]
        else:
            z[:] = rebouche.diffuse(z, trou, 500)
    if effacer and texture:
        regraine(z, trou, avant)
    fond = z.copy()
    ref = np.median(fond[trou].mean(axis=1)) if trou.any() else 128.0
    if contour is not None and contour[0] == "auto":
        # lisere de la couleur de l'encre, remplissage a mi-chemin du support
        contour = (couleur, contour[1])
        couleur = 0.6 * np.median(fond[trou], axis=0) + 0.4 * couleur
    for i, ((y0, y1, x0, x1), en, fr) in enumerate(lignes):
        s, P = calees[i]
        if not fr:
            continue
        police = polices[i]
        ce, de, le = centre_encre(en, police, graisse)
        cf, df, lf = centre_encre(fr, police, graisse)
        serre = 1.0
        Pf = Pose(*P.vecteur())
        if decale is not None:
            Pf.cy += decale[i][0]
            Pf.cx += decale[i][1]
        pl = place[i] if isinstance(place, (list, tuple)) else place
        if pl is not None and lf > le * pl:
            r = le * pl / float(lf)
            serre = max(r, serre_min)
            if r < serre:
                Pf.sx *= r / serre
                Pf.sy *= r / serre
        if droit:
            b = None
            if encres is not None:
                b = (encres[i][0] - Y0, encres[i][1] - Y0, encres[i][2] - X0, encres[i][3] - X0)
            g = _droit(masques[i], en, fr, police, pl, gauche, b, angle, graisse, serre_min)
            if decale is not None and any(decale[i]):
                g = _decale(g, decale[i][1], decale[i][0])
        else:
            if gauche:
                # le debut de l'encre francaise sur celui de l'anglaise
                cf = (df + (ce[0] - de) / serre * (P.sx / Pf.sx), cf[1])
            g = couverture_ligne(fr, police, Pf, cf, z.shape[:2], graisse=graisse, serre=serre)
        if grain:
            t = np.clip(fond.mean(axis=2) / max(ref, 1.0), 0.6, 1.3) ** grain
        else:
            t = np.ones(z.shape[:2])
        if halo is not None:
            hr, hf = halo
            lueur = np.asarray(Image.fromarray((g * 255).astype("uint8"))
                               .filter(ImageFilter.GaussianBlur(hr)), dtype=float) / 255.0
            lueur = np.clip(lueur * hf, 0, 1)
            z[:] = z * (1 - lueur[..., None]) + couleur[None, None, :] * lueur[..., None]
        if relief is not None:
            rc, rdx, rdy, rep = relief
            flanc = np.zeros_like(g)
            for k in range(1, rep + 1):
                flanc = np.maximum(flanc, _decale(g, k * rdx, k * rdy))
            z[:] = z * (1 - flanc[..., None]) + np.asarray(rc, float)[None, None, :] * flanc[..., None]
        if contour is not None:
            cc, ep = contour
            k = int(round(ep / max(Pf.sx, 1e-3)))
            if droit:
                gc = _flou_max(g, ep)
            else:
                gc = couverture_ligne(fr, police, Pf, cf, z.shape[:2], graisse=graisse + k,
                                      serre=serre)
            z[:] = z * (1 - gc[..., None]) + np.asarray(cc, float)[None, None, :] * t[..., None] * gc[..., None]
        cl = couleur if couleurs is None else np.asarray(couleurs[i], float)
        z[:] = z * (1 - g[..., None]) + cl[None, None, :] * t[..., None] * g[..., None]
        z[devant] = avant[devant]
        if verbeux and poses is None:
            print("   %-22s -> %-22s recouvrement %.2f, rotation %+.1f%s"
                  % (en, fr, s, P.theta, ", serre %.2f" % serre if serre < 1 else ""))
    if cle is not None:
        POSES.setdefault(cle, calees)
    return calees


def verticale(a, x0, x1, lettres_en, fr, police, masque, fin=None, grain=0.0,
              couleur=None, protege=None, rectangle=False, contour=None, colonnes=None,
              hauteur=None):
    """Un mot ecrit lettre sous lettre. `lettres_en` : [(y0, y1, lettre)] ;
    les lettres francaises sont reparties regulierement du centre de la
    premiere anglaise a `fin` (par defaut, le centre de la derniere)."""
    # une marge autour : un trou qui touche le bord du canevas ne se
    # rebouche pas
    Y0 = max(0, min(l[0] for l in lettres_en) - 8)
    Y1 = min(a.shape[0] - 1, max(l[1] for l in lettres_en) + 8)
    if fin is not None:
        Y1 = min(a.shape[0] - 1, max(Y1, int(fin) + 60))
    z = a[Y0:Y1 + 1, x0:x1, :3]
    avant = z.copy()
    m, intact = retouche(Y0, Y1 + 1, x0, x1, z, masque(z))
    if colonnes is not None:
        # hors de la colonne des lettres, rien n'est de l'encre (le canevas
        # deborde pour que la diffusion parte du support)
        m[:, :colonnes[0] - x0] = 0
        m[:, colonnes[1] - x0:] = 0
    poses, scores = [], []
    anglais = np.zeros(z.shape[:2])
    for y0, y1, c in lettres_en:
        mm = m[y0 - Y0:y1 - Y0 + 1]
        sc, P, ce = cale(mm, c, police, theta0=0.0)
        P.cy += y0 - Y0
        poses.append(P)
        scores.append(sc)
        anglais = np.maximum(anglais, couverture_ligne(c, police, P, ce, z.shape[:2]))
    devant = (np.asarray(protege(z)) > 0.5) if protege is not None else np.zeros(z.shape[:2], bool)
    # sous les lettres anglaises recalees, ce qui est reste identique au
    # japonais est une encre japonaise de meme teinte, recouverte : a effacer
    intact &= ~rebouche.dilate(anglais > 0.3, 2)
    # n'est efface que l'encre aux abords des lettres anglaises recalees (pas
    # les bords du support, plus sombres eux aussi)
    trou = rebouche.dilate(m > 0.2, 2) & rebouche.dilate(anglais > 0.2, 7) & ~devant & ~intact
    if couleur is None:
        couleur = np.median(z[m > 0.85], axis=0)
    couleur = np.asarray(couleur, float)
    if rectangle:
        trou = rebouche.dilate(m > 0.08, 2) & rebouche.dilate(anglais > 0.2, 7) & ~devant & ~intact
    z[:] = rebouche.diffuse(z, trou, 500)
    fond = z.copy()
    ref = np.median(fond[trou].mean(axis=1))
    if contour is not None and contour[0] == "auto":
        contour = (couleur, contour[1])
        couleur = 0.6 * np.median(fond[trou], axis=0) + 0.4 * couleur
    # l'axe : la droite des centres
    # une lettre seule se cale mal (W deborde, l s'etire) : l'echelle est
    # la mediane, isotrope, des calages surs
    sures = [P for P, sc in zip(poses, scores) if sc > 0.6] or poses
    s = np.median([np.sqrt(P.sx * P.sy) for P in sures])
    theta = np.median([P.theta for P in sures])
    # l'axe : la droite des centres
    cys = np.array([P.cy for P in poses])
    cxs = np.array([P.cx for P in poses])
    pente = np.polyfit(cys, cxs, 1) if len(poses) > 1 else (0.0, cxs[0])
    debut = cys[0]
    fin_donne = fin
    fin = (cys[-1] if fin is None else fin - Y0)
    # plus de lettres dans la meme hauteur : elles rapetissent d'autant
    pas_en = (cys[-1] - cys[0]) / float(max(len(poses) - 1, 1))
    pas_fr = (fin - debut) / float(max(len(fr) - 1, 1))
    if hauteur is not None:
        # la hauteur des capitales, relevee a la main (lettres trop petites
        # pour un calage sur)
        s = hauteur / rendu("H", police)[3]
    s *= min(1.0, pas_fr / pas_en)
    sx = sy = s
    n = len(fr)
    t = np.clip(fond.mean(axis=2) / max(ref, 1.0), 0.6, 1.3) ** grain if grain else np.ones(z.shape[:2])
    # les lettres sont empilees d'apres leur hauteur reelle, a intervalles
    # egaux, du haut de la premiere lettre anglaise au bas de la derniere
    # (ou jusqu'a `fin`) : une lettre courte apres une grande ne s'y colle pas
    formes = []
    for c in fr:
        g, ori, _, _ = rendu(c, police)
        gy, gx = np.nonzero(g > 0.5)
        formes.append((((gx.min() + gx.max()) / 2.0 - ori[0], (gy.min() + gy.max()) / 2.0 - ori[1]),
                       (gy.max() - gy.min() + 1) * sy))
    haut = lettres_en[0][0] - Y0
    bas = lettres_en[-1][1] - Y0 if fin_donne is None else fin
    total = sum(h for _, h in formes)
    ecart = max(0.0, (bas - haut - total) / float(max(n - 1, 1)))
    y = haut
    for k, c in enumerate(fr):
        centre, h = formes[k]
        cy = y + h / 2.0
        y += h + ecart
        cx = pente[0] * cy + pente[1]
        P = Pose(cx, cy, theta, sx, sy)
        gg = couverture_ligne(c, police, P, centre, z.shape[:2])
        if contour is not None:
            k = int(round(contour[1] / max(P.sx, 1e-3)))
            gc = couverture_ligne(c, police, P, centre, z.shape[:2], graisse=k)
            z[:] = z * (1 - gc[..., None]) + np.asarray(contour[0], float)[None, None, :] * t[..., None] * gc[..., None]
        z[:] = z * (1 - gg[..., None]) + couleur[None, None, :] * t[..., None] * gg[..., None]
    z[devant] = avant[devant]
    print("   %s -> %s, a la verticale (%d lettres)" % ("".join(l[2] for l in lettres_en), fr, n))


# ------------------------------------------------------------ les decors
def police(nom):
    return os.path.join(RACINE, "polices", nom)


BROSSE = police("CaveatBrush-Regular.ttf")


def bg0201aa2(a):
    """L'entree du lycee, un jour de festival."""
    panneau(a, [((0, 100, 694, 994), "Entrance", u"Entrée")], BROSSE,
            masque=union(sombre(60, 4), teinte((224, 192, 104), 25)),
            couleur=(224, 192, 104), contour=((64, 56, 32), 2))
    panneau(a, [((118, 250, 566, 1200), "Hekiho Festival", "Festival d'Hekiho")], BROSSE,
            masque=teinte((115, 165, 230), 45), place=1.0, grain=0.3)
    # le pilier de droite : Welcome a la verticale, coupe par les ballons
    panneau(a, [((128, 238, 1380, 1490), "W", "B"), ((236, 324, 1400, 1460), "e", "i"),
                ((326, 418, 1420, 1458), "l", "e")], BROSSE, masque=rouge(40),
            protege=lambda z: (np.arange(z.shape[0])[:, None] > 405 - 122) & (rouge(40)(z) > 0.5),
            grain=0.3, theta0=0.0)
    panneau(a, [((556, 630, 1716, 1920), "Welco", "Bienvenue")], BROSSE,
            masque=union(sombre(50, 5), teinte((140, 180, 225), 30)),
            couleur=(140, 180, 225), contour=((80, 82, 92), 3), gauche=True)
    panneau(a, [((636, 708, 1724, 1920), "Hopes & Dr", u"Espoirs et rêves")], BROSSE,
            masque=sombre(50), gauche=True, grain=0.4)
    panneau(a, [((664, 714, 1258, 1376), "Hekiho", u"Lycée"),
                ((712, 764, 1245, 1376), "Academy", "Hekiho")], BROSSE,
            masque=tailles(sombre(50), 3, 60, 75), place=0.9, grain=0.4, texture=True,
            protege=lambda z: sature()(z) | (np.arange(z.shape[1]) > 1372 - 1239)[None, :])
    panneau(a, [((712, 764, 382, 512), "Cultural", "Festival"),
                ((762, 808, 384, 512), "Festival", "culturel")], BROSSE,
            masque=tailles(sombre(50), 3, 60, 75), place=0.85, grain=0.4, texture=True,
            decale=[(0, -5), (0, -3)], protege=sature())
    return a


def bg0201na2(a):
    """La meme entree, de nuit et de plus loin : les piliers entiers. Celui
    de gauche dit Festival, qui ne change pas."""
    panneau(a, [((0, 100, 694, 994), "Entrance", u"Entrée")], BROSSE,
            masque=union(sombre(40, 4), teinte((88, 100, 55), 18)),
            couleur=(88, 100, 55), contour=((28, 28, 26), 2))
    panneau(a, [((112, 250, 566, 1196), "Hekiho Festival", "Festival d'Hekiho")], BROSSE,
            masque=teinte((45, 88, 158), 30), place=1.0, grain=0.3)
    verticale(a, 1385, 1495, [(128, 248, "W"), (250, 335, "e"), (338, 445, "l"),
                              (448, 530, "c"), (532, 620, "o"), (622, 722, "m"),
                              (724, 808, "e")], "Bienvenue", BROSSE,
              teinte((79, 60, 70), 22), fin=800)
    return a


COMIC = "C:/Windows/Fonts/comicbd.ttf"


def bg0202(a):
    """La salle de classe : la devise encadree au-dessus du tableau, en
    relief a peine marque. Les quatre eclairages ont le meme cadrage."""
    panneau(a, [((188, 216, 1176, 1272), "Be your", "Deviens"),
                ((214, 246, 1172, 1278), "best you", "qui tu es")], COMIC,
            masque=sombre(10, 3), contour=("auto", 1), place=1.0, incliner=False,
            graisse=6, cle="bg0202")
    return a


def rougeatre(seuil=-25, largeur=25):
    """Plus rouge que bleu, au-dela de `seuil` (r - b), sur un support bleu."""
    return lambda zz: np.clip(((zz[..., 0] - zz[..., 2]) - seuil) / float(largeur), 0, 1)


HORREUR = police("Creepster-Regular.ttf")
ARRONDIE = "C:/Windows/Fonts/ARLRDBD.TTF"
ROND = police("MPLUSRounded1c-ExtraBold.ttf")


def bg0203aa4(a):
    """Le couloir du festival : la banderole, la maison hantee (PANIC LAND,
    nom de l'attraction, reste), le panneau du cafe Gero Froggy (le nom
    reste ; Maid, sur les vitres, aussi). Sur le panneau, WELCOME devient
    ENTREZ : neuf lettres de BIENVENUE ne tiennent pas dans la colonne."""
    # les deux bouts de la banderole, puis le milieu
    for x0, x1, x2, x3 in ((462, 492, 466, 512), (684, 714, 690, 731)):
        panneau(a, [((322, 343, x0, x1), "Wel", "Bien"), ((340, 362, x2, x3), "come", "venue")],
                BROSSE, masque=rougeatre(-8, 15), place=(1.0, 1.0), incliner=False, theta0=0.0,
                rectangle=True)
    panneau(a, [((322, 370, 508, 690), "Hekiho Festival", "Festival d'Hekiho")], BROSSE,
            masque=sombre(40), place=0.97, grain=0.3)
    panneau(a, [((372, 412, 148, 266), "HAUNTED HOUSE", u"MAISON HANTÉE")], HORREUR,
            masque=rougeatre(), place=0.92, grain=0.3, texture=True)
    panneau(a, [((416, 435, 360, 410), "HAUNTED HOUSE", u"MAISON HANTÉE")], HORREUR,
            masque=rougeatre(), place=0.92, grain=0.3, texture=True)
    def bras(z):
        """Le trait du bras de la grenouille, qui croise O, M, E (releve sur
        l'original japonais : bord droit x = 147 - 0,47 (y - 860))."""
        ys, xs = np.mgrid[0:z.shape[0], 0:z.shape[1]]
        y, x = ys + 752, xs + 82
        droit = 147 - 0.47 * (y - 860)
        large = np.where(y < 900, 13, 6)
        return (y >= 850) & (x <= droit + 1) & (x >= droit - large) & (z.mean(axis=2) < 110)
    verticale(a, 82, 136, [(760, 783, "W"), (785, 810, "E"), (812, 840, "L"), (842, 868, "C"),
                           (870, 897, "O"), (898, 921, "M"), (922, 940, "E")], "ENTREZ",
              ROND, sombre(30, 4), contour=("auto", 1), colonnes=(90, 124), protege=bras,
              hauteur=19, fin=930)
    panneau(a, [((890, 911, 132, 196), "Feel free", "Tu peux"),
                ((906, 928, 140, 201), "to pet it.", "le caresser.")], ROND,
            masque=sombre(30, 4), contour=("auto", 1), place=(1.0, 1.15), incliner=False,
            texture=True, decale=[(0, 0), (0, -4)])
    return a


KALAM = police("Kalam-Bold.ttf")


def bg0205aa2(a):
    """Le gymnase : la banderole au-dessus de la scene."""
    panneau(a, [((370, 400, 900, 1170), "Third Annual Hekiho Festival",
                 u"Troisième festival d'Hekiho")], KALAM,
            masque=sombre(25, 4), place=1.0, grain=0.2)
    return a


def bg0208(a):
    """La salle du club de journalisme : l'etiquette du plan de Shibuya
    punaise au mur (Myriad), penchee de 6 degres (pente du filet du bas) :
    on la traite redressee. Le millesime rouge reste. Les douze eclairages
    ont l'etiquette au meme endroit."""
    def droite(z):
        rouges = lambda zz: rebouche.dilate(plus_rouge(20)(zz) > 0.3, 1)
        l = z[19:63, 15:70].mean(axis=2)
        encre = np.median(z[19:63, 15:70][l < np.percentile(l, 4)], axis=0)
        panneau(z, [((19, 38, 15, 68), "Shibuya", "Gare de"),
                    ((37, 53, 17, 56), "Station", "Shibuya"),
                    ((53, 63, 18, 70), "SURROUNDING AREA MAP", "PLAN DES ENVIRONS")],
                [MYRIAD, MYRIAD, MYRIAD_SEMI], masque=sombre(20, 3), place=(1.0, 1.0, 0.95),
                droit=True, couleur=encre, verbeux=False,
                # le millesime rouge, et le filet du cadre au-dessus de la
                # premiere ligne (rangees 17 et 18 de la zone redressee ; le
                # canevas commence 6 rangees au-dessus de la ligne, en 13)
                protege=lambda zz: rouges(zz) | (np.arange(zz.shape[0]) < 19 - 13)[:, None],
                # boites d'encre relevees dans la zone redressee ; le francais
                # est reduit plutot que serre, et la queue du y de Shibuya
                # (deuxieme ligne, ici) demande un peu d'air au-dessous
                encres=[(21, 36, 18, 65), (38, 51, 20, 55), (55, 60, 21, 68)],
                serre_min=0.97, decale=[(-1, 0), (-2, 0), (1, 0)])
        return z
    return redresse(a, (255, 335, 0, 95), 6.0, droite)


def bg0426aa(a):
    """La devanture du fleuriste. SUN BLOOMS est l'enseigne : elle reste."""
    panneau(a, [((160, 198, 965, 1205), "we ship nationwide", "livraison nationale")], BROSSE,
            masque=sombre(40, 6), place=1.0, grain=0.25, fuite=True, graisse=2)
    return a


def vert(seuil=30):
    """Une face verte (g au-dessus de r) sur un support bleu-gris."""
    return lambda zz: np.clip(((zz[..., 1] - zz[..., 0]) - seuil) / 20.0, 0, 1) *         (zz[..., 1] > zz[..., 2] - 15)


ETROITE = police("RobotoCondensed-Bold.ttf")


def lettres_relief(a, zone, en, fr, police, masque, couleur_face, flanc, place=1.0,
                   protege=None, droite=False, degre=2, x_bords=None):
    """Des lettres en volume sur une ligne courbe (une enseigne sur un auvent
    arrondi) : face et flanc. `flanc` = (couleur, dx, dy, epaisseur)."""
    y0, y1, x0, x1 = zone
    z = a[y0:y1, x0:x1, :3]
    avant = z.copy()
    m, intact = retouche(y0, y1, x0, x1, z, masque(z))
    ys, xs = np.nonzero(m > 0.5)
    bx0, bx1 = (xs.min(), xs.max()) if x_bords is None else (x_bords[0] - x0, x_bords[1] - x0)
    ph, pb = _bords(m, bx0, bx1, degre)
    fc, fdx, fdy, fep = flanc
    # le trou : la face, et son flanc
    face = rebouche.dilate(m > 0.25, 1)
    trou = face.copy()
    for k in range(1, fep + 2):
        trou |= _decale(face.astype(float), k * fdx, k * fdy) > 0.3
    # et tout ce que le CoZ a repeint aux abords (ombres, anticrenelage)
    trou |= ~intact & rebouche.dilate(trou, 3) if intact.any() else trou
    devant = (np.asarray(protege(z)) > 0.5) if protege is not None else np.zeros(z.shape[:2], bool)
    trou &= ~devant & ~intact
    z[:] = rebouche.diffuse(z, trou, 600)
    # le francais : meme ruban, centre, au plus `place` fois l'anglais
    e0, e1 = xs.min(), xs.max()
    le = e1 - e0
    g0, _, _, cap0 = rendu(en, police)
    g1, _, _, cap1 = rendu(fr, police)
    gy, gx = np.nonzero(g0 > 0.5)
    hy, hx = np.nonzero(g1 > 0.5)
    rapport = (hx.max() - hx.min()) / float(gx.max() - gx.min())
    lf = le * min(rapport, place)
    if droite:
        # un mot coupe par le bord gauche : on cale sur sa fin
        f0, f1 = e1 - lf, e1
    else:
        c = (e0 + e1) / 2.0
        f0, f1 = c - lf / 2.0, c + lf / 2.0
    g = ruban(z.shape[:2], fr, police, ph, pb, f0, f1)
    fl = np.zeros_like(g)
    for k in range(1, fep + 1):
        fl = np.maximum(fl, _decale(g, k * fdx, k * fdy))
    z[:] = z * (1 - fl[..., None]) + np.asarray(fc, float)[None, None, :] * fl[..., None]
    z[:] = z * (1 - g[..., None]) + np.asarray(couleur_face, float)[None, None, :] * g[..., None]
    z[devant] = avant[devant]
    print("   %-24s -> %-28s ruban, %d px (anglais %d)" % (en, fr, f1 - f0, le))


def bg0501aa(a):
    """La facade de l'hopital : les lettres en volume sur l'auvent."""
    lettres_relief(a, (282, 375, 765, 1225), "AH TOKYO GENERAL HOSPITAL",
                   u"HÔPITAL GÉNÉRAL AH DE TOKYO", ETROITE, vert(30),
                   (125, 195, 175), ((45, 60, 95), -1, 1, 3), place=1.04)
    return a


def bg0501na1(a):
    """L'hopital de nuit, vu de plus pres : lettres blanches eclairees."""
    lettres_relief(a, (282, 375, 765, 1225), "AH TOKYO GENERAL HOSPITAL",
                   u"HÔPITAL GÉNÉRAL AH DE TOKYO", ETROITE, clair(60, 5),
                   (242, 252, 238), ((70, 30, 40), 1, 1, 2), place=1.04)
    return a


SEGOE = "C:/Windows/Fonts/segoeui.ttf"


def bg0502(a):
    """L'entree de l'hopital : RECEPTION au-dessus du comptoir, en fuite.

    Les deux eclairages ont le meme cadrage : on cale sur la nuit, ou les
    lettres sont nettes. Le jour, elles rayonnent : on efface tout ce qui
    est clair autour des lettres de la nuit."""
    lignes = [((120, 218, 1150, 1320), "RECEPTION", "ACCUEIL")]
    nuit = np.asarray(Image.open(os.path.join(os.path.dirname(RACINE), "reference",
                                              "bg0502na.png")).convert("RGB")).astype(float)
    net = tailles(clair(50, 6), 18, 60, 45)
    lettres = rebouche.dilate(net(nuit[120:218, 1150:1320]) > 0.3, 4)
    if "bg0502" not in POSES:
        global JP
        jp, JP = JP, japonais("bg0502na")
        panneau(nuit, lignes, SEGOE, masque=net, fuite=True, cle="bg0502", verbeux=False)
        JP = jp

    def masque(z):
        m = np.clip((z.mean(axis=2) - 130) / 40.0, 0, 1)
        return m * lettres if m.mean() > net(z).mean() * 1.5 else net(z)
    jour = a[120:218, 1150:1320].mean() > nuit[120:218, 1150:1320].mean() + 20
    panneau(a, lignes, SEGOE, masque=masque, fuite=True, marge=3, cle="bg0502",
            halo=(2.5, 1.2) if jour else None)
    return a


def bg0504(a):
    """Le couloir de l'hopital : l'armoire a incendie (Myriad), plaque et
    inscription penchees de -2,5 degres : traitees redressees. Les trois
    eclairages ont le meme cadrage."""
    def plaque(z):
        panneau(z, [((15, 33, 11, 102), "FIRE DEPT. VALVE", "ROBINET POMPIERS"),
                    ((34, 45, 12, 101), "FOR USE BY TRAINED PERSONS ONLY",
                     u"RÉSERVÉ AU PERSONNEL FORMÉ")], [MYRIAD_SEMI, MYRIAD],
                masque=clair(18, 3), place=(0.94, 1.0), droit=True, texture=True,
                encres=[(18, 31, 13, 100), (36, 43, 15, 98)], verbeux=False)
        return z
    redresse(a, (680, 740, 875, 995), -2.5, plaque)

    def robinet(z):
        # le metal est uni : tout le rectangle du mot est efface
        trou = np.zeros(z.shape[:2], bool)
        trou[7:34, 12:92] = True
        couleur = np.median(z[13:27, 18:85][sombre(15, 4)(z[13:27, 18:85]) > 0.8], axis=0)
        z[:] = rebouche.diffuse(z, trou, 600)
        panneau(z, [((10, 32, 14, 90), "WATER TAP", "EAU")], MYRIAD,
                masque=sombre(15, 4), place=1.0, droit=True, effacer=False,
                couleur=couleur, encres=[(13, 27, 18, 85)], verbeux=False)
        return z
    redresse(a, (838, 882, 880, 985), -2.5, robinet)
    return a


def vert_sombre(seuil=12):
    return lambda zz: np.clip(((zz[..., 1] - zz[..., 0]) - seuil) / 8.0, 0, 1)


def bg0509(a):
    """Le hall de l'hopital : le comptoir des infirmieres (en relief, coupe
    par le bord gauche : on garde la fin du mot) et le panneau suspendu."""
    lettres_relief(a, (220, 332, 0, 362), "SES STATION", u"INFIRMIÈRES",
                   ETROITE, union(tailles(vert_sombre(12), 20, 60, 45),
                                  lambda z: vert_sombre(12)(z) * (np.arange(z.shape[1]) < 16)[None, :]
                                  * (np.arange(z.shape[0]) < 75)[:, None]), (25, 54, 42),
                   ((14, 22, 20), 1, 1, 3), place=1.3, droite=True, degre=1,
                   x_bords=(21, 355))
    panneau(a, [((222, 248, 512, 655), "GASTROENTEROLOGY", u"GASTRO-ENTÉROLOGIE"),
                ((222, 248, 710, 800), "ELEVATORS", "ASCENSEURS")], MYRIAD,
            masque=sombre(30, 5), place=(1.0, 1.1), droit=True, serre_min=0.92, verbeux=False,
            encres=[(227, 241, 514, 655), (228, 243, 710, 795)])
    return a


INTER = police("Inter-Black.ttf")
MYRIAD = police("SourceSans3-Bold.ttf")
MYRIAD_SEMI = police("SourceSans3-Semibold.ttf")
SEGOE_GRAS = "C:/Windows/Fonts/segoeuib.ttf"


def espace(texte, blanc=u" "):
    """Le texte espace lettre a lettre (les capitales espacees d'une
    enseigne) ; un espace devient deux."""
    return blanc.join(texte.replace(" ", "  "))


def bg0601(a):
    """La plaque de la clinique Aoba, a l'entree (Myriad), penchee de -5,7
    degres : traitee redressee. Les horaires (AM/PM) sont ceux de l'original
    japonais ; seuls les jours, en tete de la derniere ligne, sont traduits.
    Meme cadrage pour les quatre eclairages ; les couleurs de l'encre sont
    relevees sur chacun."""
    def droite(z):
        l = z[16:31, 18:128].mean(axis=2)
        noir = np.median(z[16:31, 18:128][l < np.percentile(l, 10)], axis=0)
        bas = z[33:45, 16:130]
        lb = bas.mean(axis=2)
        bleu_ = np.median(bas[lb < np.percentile(lb, 15)], axis=0)
        contraste = max(20.0, (np.percentile(l, 70) - noir.mean()) * 0.6)
        panneau(z, [((12, 33, 14, 137), "AOBA CLINIC", "CLINIQUE AOBA"),
                    ((32, 46, 14, 134), espace("PEDIATRIC CARE"), espace(u"PÉDIATRIE")),
                    ((81, 97, 13, 51), "(FRI&SAT", "(VEN&SAM")],
                [MYRIAD, MYRIAD_SEMI, MYRIAD], masque=sombre(contraste, 4),
                place=(1.0, 1.0, 1.0), droit=True, couleurs=[noir, bleu_, noir],
                encres=[(16, 30, 18, 128), (33, 44, 16, 130), (83, 95, 15, 49)],
                tout_coz=True, verbeux=False)
        return z
    return redresse(a, (335, 450, 1000, 1150), -5.7, droite)




def bg0604(a):
    """L'accueil de la clinique : RECEPTION au-dessus du guichet, et
    l'affiche des horaires de pediatrie (les heures restent)."""
    panneau(a, [((176, 216, 1170, 1275), "RECEPTION", "ACCUEIL")], SEGOE,
            masque=tailles(sombre(40, 4), 8, 40, 30), fuite=True, cle="bg0604")
    panneau(a, [((397, 413, 1412, 1494), "Pediatrics", "Horaires des"),
                ((410, 425, 1412, 1494), "Consultation", "consultations"),
                ((423, 438, 1412, 1494), "Hours", u"de pédiatrie")], MYRIAD,
            masque=sombre(18, 4), droit=True, place=(1.3, 1.02, 2.2), verbeux=False, tout_coz=True,
            decale=[(-1, 0), (-1, 0), (1, 0)],
            encres=[(400, 410, 1428, 1482), (412, 422, 1418, 1490), (425, 435, 1440, 1472)])
    panneau(a, [((470, 484, 1412, 1494), "Closed during", u"Fermé les"),
                ((481, 495, 1412, 1494), "public holidays", u"jours fériés")], MYRIAD,
            masque=sombre(18, 4), droit=True, place=1.0, verbeux=False, tout_coz=True,
            encres=[(474, 481, 1425, 1486), (483, 491, 1423, 1488)])
    return a


# ------------------------------------------------------------ fichiers
def _depuis(base, retouche, zone):
    """Une variante trop sombre pour un calage : on fait la retouche sur
    l'image de base et on la reporte (transfere)."""
    def f(a):
        b = np.asarray(Image.open(reference(base)).convert("RGB")).astype(float)
        global JP
        jp, JP = JP, japonais(base)
        apres = retouche(b.copy())
        JP = jp
        e = transfere(b, apres, a, zone)
        print("   reporte depuis %s (ecart de couleur %.1f)" % (base, e))
        return a
    return f


FICHIERS = {
    "bg0201aa2": bg0201aa2,
    "bg0201na2": bg0201na2,
    "bg0202aa": bg0202, "bg0202aa2": bg0202, "bg0202aa3": bg0202, "bg0202na": bg0202,
    "bg0203aa4": bg0203aa4,
    "bg0205aa2": bg0205aa2,
    "bg0426aa": bg0426aa,
    "bg0501aa": bg0501aa,
    "bg0501na": _depuis("bg0501aa", bg0501aa, (275, 380, 760, 1230)),
    "bg0501na1": bg0501na1, "bg0501na2": bg0501na1,
    "bg0502aa": bg0502, "bg0502na": bg0502,
    "bg0504na": bg0504, "bg0504na1": bg0504, "bg0504na2": bg0504,
    "bg0509na": bg0509, "bg0509na1": bg0509,
    "bg0601aa": bg0601, "bg0601ar": bg0601, "bg0601ea": bg0601, "bg0601na": bg0601,
    "bg0604aa": bg0604, "bg0604ea": bg0604, "bg0604na": bg0604,
}
for _n in ("aa1", "aa2", "aa4", "aa5", "aa6", "ac1", "ac2", "ea1", "ea2", "na", "na1", "na3"):
    FICHIERS["bg0208" + _n] = bg0208
# bg0302aa : l'enseigne Fairy's Dance, nom propre (garde dans le texte du
# jeu) ; rien a traduire.

JEU = "D:/SteamLibrary/steamapps/common/CHAOS;CHILD/languagebarrier/"
DEPOT = os.path.dirname(os.path.dirname(RACINE))


def reference(nom):
    import mpk
    dossier = os.path.join(DEPOT, "cg", "reference")
    c = os.path.join(dossier, nom + ".png")
    if not os.path.exists(c):
        f = io.open(JEU + "backup0data.mpk", "rb")
        T = dict((e.nom, e) for e in mpk.lit_table(f) if e.nom)
        io.open(c, "wb").write(mpk.lit(f, T[nom + ".png"]))
    return c


def japonais(nom):
    c = os.path.join(DEPOT, "cg", "reference", "jp", nom + ".png")
    return np.asarray(Image.open(c).convert("RGB")).astype(float) if os.path.exists(c) else None


# le pilier de nuit : l'anglais y recouvre des caracteres japonais de la
# meme encre, la comparaison au japonais n'y aide pas
SANS_JAPONAIS = ("bg0201na2",)


def traite(nom, a):
    """La retouche de `nom` sur l'image a, avec son original japonais."""
    global JP
    JP = None if nom in SANS_JAPONAIS else japonais(nom)
    try:
        return FICHIERS[nom](a)
    finally:
        JP = None


def main():
    vises = [v for v in sys.argv[1:] if not v.startswith("--")]
    noms = [n for n in sorted(FICHIERS) if not vises or any(v in n for v in vises)]
    faits = []
    for nom in noms:
        print(nom)
        im = Image.open(reference(nom))
        a = np.asarray(im.convert("RGB")).astype(float)
        a = traite(nom, a)
        sortie = Image.fromarray(np.clip(np.round(a), 0, 255).astype("uint8"))
        if im.mode == "RGBA":
            sortie.putalpha(im.split()[3])
        c = os.path.join(DEPOT, "cg", "c0data", nom + ".png")
        sortie.save(c, optimize=True, compress_level=9)
        faits.append(c)
    if "--install" in sys.argv and faits:
        import remplace
        remplace.remplace(JEU + "c0data.mpk", faits)


if __name__ == "__main__":
    main()
