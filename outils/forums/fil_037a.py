# -*- coding: utf-8 -*-
"""cc_pbg037a : le meme fil que cc_pbg037ab, mais dans la fenetre du navigateur.

Le forum y est rendu a la meme taille, simplement decale de (+30, +58) et pose
dans une image de 1920x2178. Le texte est donc identique : on reprend CORPS.
"""
from fil_037ab import CORPS, NOIR, ROUGE      # noqa: F401

ZONE = (60, 1840)      # bornes du cadre du forum dans la fenetre
BORD = 1840

TITRE_BLOC = {
    "zone": (70, 104, 1010, 156),
    "taille": 20,
    "lignes": [
        (150, 126, [("[Haida Riko] Le tueur derrière le Retour des attaques", ROUGE)]),
        (78, 142, [("[Society]", NOIR)], 16),
        (150, 151, [("New Generation part en fumée [Suicide ? Meurtre ?] 8", ROUGE)]),
    ],
}
