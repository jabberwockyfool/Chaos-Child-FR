# -*- coding: utf-8 -*-
"""Les bandeaux de commandes restes en anglais : data01 (les bandeaux
violets des choix, celui des pages de l'aide) et tipschips (la liste des
TIPS).

Ces deux textures avaient deja ete retouchees par l'equipe (NEW TIP, le titre
et les onglets des TIPS), en DXT1 : on part de ces versions, mises de cote
dans cg/reference/equipe/. Le DXT1 n'a qu'une transparence tout ou rien,
que le decodeur ignore ; les bandeaux sont opaques, et dds.ecrit refuse de
reencoder un bloc qui ne l'est pas.
"""
import habillage

# ((Y0, Y1) du bandeau, (y0, y1) des capitales, [((debut, fin, icone
# suivante), anglais, francais)])
BANDEAUX = {
    "data01.dds": [
        ((1121, 1170), (1129, 1159), [((106, 197, 1100), "SCROLL", u"DÉFILER")]),
        ((1177, 1226), (1186, 1216), [
            ((106, 193, 231), "SELECT", "CHOISIR"),
            ((268, 383, 1100), "CONFIRM", "VALIDER"),
        ]),
        ((1240, 1289), (1249, 1279), [
            ((1409, 1577, 1614), "CHANGE PAGE", "FEUILLETER"),
            ((1658, 1721, 2400), "BACK", "RETOUR"),
        ]),
    ],
    "tipschips.dds": [
        ((1052, 1101), (1061, 1091), [
            ((110, 196, 234), "SELECT", "CHOISIR"),
            ((298, 460, 497), "SCROLL TEXT", u"DÉFILER"),
            ((563, 605, 643), "TAB", "ONGLET"),
            ((680, 795, 832), "CONFIRM", "VALIDER"),
            ((876, 940, 1500), "BACK", "RETOUR"),
        ]),
    ],
}


def bandeaux(a, nom):
    for lignes, cap, mots in BANDEAUX[nom]:
        habillage.bandeau(a, lignes, cap, mots)
    return a
