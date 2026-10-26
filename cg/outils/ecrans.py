# -*- coding: utf-8 -*-
"""Les ecrans d'interface, stockes en .dds (DXT1 / DXT5).

Le texte y est pose sur des aplats (tache d'encre, bandeau), donc l'effacement
se fait a la couleur du fond, relevee autour du mot. On ne reencode que les
blocs 4 x 4 touches (voir `dds.py`), le reste du fichier est recopie tel quel.

    python cg/outils/ecrans.py [sysmesswindow] [gsysmes] [loadmenu] [--install]
"""
import io
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

RACINE = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.dirname(os.path.dirname(RACINE))
sys.path.insert(0, RACINE)
import dds          # noqa: E402
import mpk          # noqa: E402
import remplace     # noqa: E402
import aide         # noqa: E402
import barres       # noqa: E402
import bobines      # noqa: E402
import carte        # noqa: E402
import config       # noqa: E402
import menuchip     # noqa: E402
import titre        # noqa: E402
import habillage    # noqa: E402

JEU = "D:/SteamLibrary/steamapps/common/CHAOS;CHILD/languagebarrier/"
REFERENCE = JEU + "backup0data.mpk"
SORTIE = os.path.join(DEPOT, "cg", "c0data")
IMPACT = "C:/Windows/Fonts/impact.ttf"
CONDENSE = 0.80          # l'original est plus etroit que l'Impact nu

# (boite du texte, anglais, francais). OK reste OK.
TABLES = {
    "sysmesswindow.dds": [
        ((1336, 1392, 702, 777), "YES", "OUI"),
        ((1336, 1392, 936, 1011), "YES", "OUI"),
        # la tache pleine ne fait que 93 px : on bride NON a 76
        ((1211, 1267, 1166, 1222), "NO", "NON", 76),
        ((1413, 1469, 1166, 1222), "NO", "NON", 76),
    ],
}


def rendu(texte, hauteur, police=IMPACT, condense=CONDENSE):
    """Le mot a la hauteur voulue, resserre comme dans l'original."""
    for corps in range(10, 200):
        ft = ImageFont.truetype(police, corps)
        im = Image.new("L", (900, 300), 0)
        ImageDraw.Draw(im).text((30, 30), texte, 255, font=ft)
        a = np.asarray(im, dtype=float) / 255.0
        ys, xs = np.nonzero(a > 0.5)
        if ys.max() - ys.min() + 1 >= hauteur:
            break
    g = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    cible = (max(1, int(round(g.shape[1] * condense))), hauteur)
    return np.asarray(Image.fromarray((g * 255).astype("uint8"))
                      .resize(cible, Image.LANCZOS), dtype=float) / 255.0


def traite(chemin, table):
    t = dds.lit(chemin)
    a = t["rgba"].astype(float).copy()
    for entree in table:
        (y0, y1, x0, x1), en, fr = entree[:3]
        large_max = entree[3] if len(entree) > 3 else None
        bande = a[y0:y1, x0:x1]
        # couleur du texte : le coeur ; couleur du fond : le pourtour de la boite
        M = 10
        cadre = a[max(0, y0 - M):y1 + M, max(0, x0 - M):x1 + M]
        anneau = np.ones(cadre.shape[:2], bool)
        anneau[M:M + (y1 - y0), M:M + (x1 - x0)] = False
        fond = np.median(cadre[anneau], axis=0)
        # le texte est ce qui s'ecarte le plus du fond
        ecart = np.abs(bande[..., :3] - fond[:3]).max(axis=2)
        couleur = bande[ecart > 0.7 * ecart.max()].mean(axis=0)

        a[max(0, y0 - 4):y1 + 4, max(0, x0 - 4):x1 + 4] = fond
        g = rendu(fr, y1 - y0)
        if large_max and g.shape[1] > large_max:
            g = rendu(fr, y1 - y0, condense=CONDENSE * large_max / float(g.shape[1]))
        h, w = g.shape
        yy = y0
        xx = (x0 + x1 - w) // 2
        bloc = a[yy:yy + h, xx:xx + w]
        m = g[..., None]
        bloc[:] = bloc * (1 - m) + couleur * m
        print("   %-4s -> %-4s  %3d px (anglais %3d)" % (en, fr, w, x1 - x0))
    return t, a


CARLITO = "C:/Windows/Fonts/Carlito-Regular.ttf"


def lettre(c, police, corps, hauteur, largeur=None):
    """Un glyphe seul, recadre, ramene a la hauteur (et largeur) voulues."""
    ft = ImageFont.truetype(police, corps)
    im = Image.new("L", (300, 300), 0)
    ImageDraw.Draw(im).text((40, 40), c, 255, font=ft)
    g = np.asarray(im, dtype=float) / 255.0
    ys, xs = np.nonzero(g > 0.02)
    g = g[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    cible = (largeur or g.shape[1], hauteur)
    return np.asarray(Image.fromarray((g * 255).astype("uint8"))
                      .resize(cible, Image.LANCZOS), dtype=float) / 255.0


def gsysmes(a):
    """Confirm -> Confirmer, dans les deux etats du bouton.

    Le texte est cale a gauche : on garde "Confirm" au pixel pres et on
    ajoute "er". Le r est recopie de l'original ; le e, absent, vient de
    Carlito, dont le o a la meme graisse que l'original (meme quantite
    d'encre), ramene aux proportions du o d'origine.

    Etat clair (a droite) : noir sur blanc. Etat sombre (a gauche) : blanc,
    le texte dans l'alpha, avec un reste du japonais sous le C ; on le
    reconstruit donc a partir de l'etat clair, decale de 290 px.
    """
    Y0, Y1, X0, X1 = 1100, 1175, 310, 550        # sans toucher aux filets du cadre
    DECALE = 290
    cov = 1 - a[Y0:Y1, X0:X1, :3].mean(axis=2) / 255.0
    ys, xs = np.nonzero(cov > 0.5)
    x0 = xs.min()                                 # debut du C
    o = cov[:, x0 + 26:x0 + 50]
    oy, ox = np.nonzero(o > 0.5)
    o_h = oy.max() - oy.min() + 1
    o_w = ox.max() - ox.min() + 1
    o_y = oy.min()
    r = cov[:, x0 + 104:x0 + 120].copy()          # le r, avec sa marge
    m_fin = x0 + 156                              # dernier pixel du m

    e = lettre("e", CARLITO, 53, o_h, o_w)
    xe = m_fin + 5
    cov[o_y:o_y + o_h, xe:xe + o_w] = np.maximum(
        cov[o_y:o_y + o_h, xe:xe + o_w], e)
    rx, = np.nonzero((r > 0.25).any(axis=0))
    r = r[:, rx.min():rx.max() + 1]
    xr = xe + o_w + 3
    cov[:, xr:xr + r.shape[1]] = np.maximum(cov[:, xr:xr + r.shape[1]], r)

    gris = 255.0 * (1 - cov)
    for k in range(3):
        a[Y0:Y1, X0:X1, k] = gris
    g = a[Y0:Y1, X0 - DECALE:X1 - DECALE]
    g[..., :3] = 255.0
    g[..., 3] = 255.0 * cov
    print("   Confirm -> Confirmer  %d px (anglais %d)"
          % (xr + r.shape[1] - x0, m_fin + 1 - x0))
    return a


SPECIAUX = {"gsysmes.dds": gsysmes, "backlog.dds": habillage.backlog,
            "clearlist.dds": habillage.clearlist,
            "library.dds": habillage.library,
            "music.dds": habillage.music,
            "movmenu.dds": bobines.menu,
            "mapbg.dds": carte.plan,
            "menuchip.dds": menuchip.menu,
            "help00_steam.dds": aide.clavier,
            "help01.dds": aide.manette,
            "config.dds": config.ecran,
            "title_chip.dds": titre.titre_chip,
            "title_bg.dds": titre.titre_bg}
for _n in habillage.LOGO:
    SPECIAUX[_n] = (lambda n: lambda a: habillage.menu(a, n))(_n)
for _n in barres.BANDEAUX:
    SPECIAUX[_n] = (lambda n: lambda a: barres.bandeaux(a, n))(_n)
# deja retouchees par l'equipe : on part de leur version, pas de l'anglais
EQUIPE = ("data01.dds", "tipschips.dds")


def reference(nom):
    dossier = os.path.join(DEPOT, "cg", "reference")
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    if nom in EQUIPE:
        return os.path.join(dossier, "equipe", nom)
    c = os.path.join(dossier, nom)
    if not os.path.exists(c):
        f = io.open(REFERENCE, "rb")
        T = dict((e.nom, e) for e in mpk.lit_table(f) if e.nom)
        io.open(c, "wb").write(mpk.lit(f, T[nom]))
    return c


def main():
    vises = [a for a in sys.argv[1:] if not a.startswith("--")]
    noms = [n for n in list(TABLES) + list(SPECIAUX) if not vises or any(v in n for v in vises)]
    faits = []
    for nom in sorted(noms):
        print(nom)
        ref = reference(nom)
        if nom in SPECIAUX:
            t = dds.lit(ref)
            a = SPECIAUX[nom](t["rgba"].astype(float).copy())
        else:
            t, a = traite(ref, TABLES[nom])
        c = os.path.join(SORTIE, nom)
        io.open(c, "wb").write(io.open(ref, "rb").read())
        n, tot = dds.ecrit(c, t, np.clip(a, 0, 255).astype("uint8"))
        print("   %d blocs reencodes sur %d (%.2f %%)" % (n, tot, 100.0 * n / tot))
        faits.append(c)
    if "--install" in sys.argv and faits:
        print()
        remplace.remplace(JEU + "c0data.mpk", faits)


if __name__ == "__main__":
    main()
