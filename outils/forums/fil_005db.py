# -*- coding: utf-8 -*-
"""cc_pbg005db : fil @chan « Watabe Tomoaki est mort mdr »."""
from page import CJK

NOIR = (0, 0, 0)
ROUGE = (255, 0, 0)

# l'art ASCII du message 41 : on n'y touche pas
SAUTER = [(3700, 3900)]

DIEU = "Les Stickers Sumo sont Dieu."
SPAM = (DIEU + " ") * 4

TITRE = [("[Bad News] ", NOIR), ("Watabe Tomoaki est mort mdr", ROUGE)]

CORPS = [
    # 1 (dépêche)
    "D'après un communiqué de la police métropolitaine de Shibuya, dans l'après-midi du 10 vers 13h00,",
    "Watabe Tomoaki a été retrouvé mort.",
    "La police de Shibuya envisage aussi bien l'accident que le meurtre ou le suicide, et cherche à établir",
    "la cause de la mort de Watabe-san ainsi que d'éventuelles maladies.",
    "Premier !",                                                   # 2
    "PREMIER MESSAGE",                                             # 3
    "Repose en paix. (Je saute l'art ASCII)",                       # 4
    "Repose en paix mdrr",                                          # 5
    "Cette joie mauvaise me fait bander.",                          # 6
    "Il a dansé avec la malchance, hein ?",                         # 7
    "Repose en paix.",                                              # 8
    "BIEN FAIT !",                                                  # 9
    "Putain.",                                                      # 10
    "Qui ça ?",                                                     # 11
    "RIP.",                                                         # 12
    "Repose En paix ptdrrr",                                        # 13
    "Ces yeux, à qui sont-ils ?",                                   # 14
    "Repose en paix ptdr",                                          # 15
    "Il en a trop appris ?",                                        # 16
    "Les ténèbres des Stickers Sumo sont profondes.",               # 17
    ("Attendez, là ça fait vraiment peur.",                         # 18
     "Pourquoi vous rigolez, vous ?"),
    "Quelqu'un a forcément dû le tuer, non ?",                      # 19
    "Puuuutaaaain de meeeerde",                                     # 20
    "On est le putain de dix aujourd'hui !",                        # 21
    "La Folie New Gen ?",                                           # 22
    "Alors ça a commencé ?",                                        # 23
    "Repose en paix.",                                              # 24
    ("Les Stickers Sumo sont dieu.",                                # 25
     "Aucune objection admise."),
    "Content que ce connard soit mort.",                            # 26
    "LEQUEL D'ENTRE VOUS A FAIT ÇA !!!111",                         # 27
    "BIEN FAAAAIIIT POUUUUUUUUUR TOOOOOOIII !",                     # 28
    "Hein ? Donc les dates correspondent encore ?",                 # 29
    ">>14",                                                         # 30
    "Ces yeux sont les yeux de Dieu ?",
    ("Pourquoi vous le détestez autant ?",                          # 31
     "C'est juste un plagiaire minable."),
    "Repose en paix.",                                              # 32
    "Bon, c'était qui ce type, déjà ?",
    ("Sortez pas une édition spéciale juste parce que ce crétin est mort.",   # 33
     "J'étais en train d'enregistrer Conan, putain !"),
    "Adorez les Stickers Sumo.",                                    # 34
    "Crève.",                                                       # 35
    ("Ça le prouve.",                                               # 36
     "Le prochain sera le 23/10."),
    "Les Stickers Sumo sont Dieu.",                                 # 37
    "Aucune objection admise.",
    "Repentez-vous de vos péchés.",
    "Il y aura d'autres victimes.",
    ("Tu te fous de moi mdr",                                       # 38
     "Le type qui couvre toute cette histoire finit lui-même tué ?"),
    "Les Stickers Sumo sont Dieu.",                                 # 39
    "Les Stickers Sumo sont Dieu.",                                 # 40
    "Les Stickers Sumo sont Dieu.",
    [("C'est le Retour de la Folie New Gen, et je peux pas le SUPPORTER ! ", NOIR),   # 41
     ("(ll ´ （ｴ） ` ll)", NOIR, CJK)],
    # (art ASCII saute)
    [("Retour de la Folie N00d Gen 1 Sans-Regard ", NOIR), ("(o ´▽` )o/", NOIR, CJK)],
    [("Retour de la Folie N00d Gen 2 Fuite Audio ", NOIR), ("♪＼(| ` □ ´|＼)", NOIR, CJK)],
    [("Retour de la Folie N00d Gen 3 Ronde macabre ", NOIR), ("ｷﾀｷﾀ(@□@)ｷﾀｷﾀ", NOIR, CJK)],
    "Retour de la Folie N00d Gen 4 (en débat)",
    [("...à suivre ? ", NOIR), ("(゜ ロ゜ )!!", NOIR, CJK)],
    ">>41",                                                         # 42
    "T'es en retard.",
    ">>41",                                                         # 43
    "C'est exactement ce que je viens voir.",
    "Les Stickers Sumo sont Dieu.",                                 # 44
    "Les Stickers Sumo sont Dieu.",
    "Les Stickers Sumo sont Dieu.",
    "Ça s'est fini exactement comme Watabe l'avait dit, hein ?",    # 45
    "Les Stickers Sumo sauveront le monde.",                        # 46
    "Va troller ailleurs.",                                         # 47
    "Watabe s'est peut-être tué pour prouver que son article disait vrai ?",   # 48
    "Si c'est le cas, il a mon respect.",
    "Un carnaval miraculeux est sur le point de commencer !",       # 49
] + [DIEU] * 7 + [                                                  # 50
    "Qu'est-ce qui SE PASSE à Shibuya ?",                           # 51
] + [SPAM] * 21 + [                                                 # 52, 53, 54
    "Repose en paix.",                                              # 55
]
