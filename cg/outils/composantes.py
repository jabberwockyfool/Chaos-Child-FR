# -*- coding: utf-8 -*-
"""Etiquetage des composantes connexes (4-voisinage), sans scipy."""
from collections import deque

import numpy as np


def composantes(m):
    """Rend (etiquettes, liste de (n, y0, y1, x0, x1)) ; etiquette 0 = fond."""
    h, w = m.shape
    lab = np.zeros((h, w), int)
    infos = []
    for y, x in zip(*np.nonzero(m)):
        if lab[y, x]:
            continue
        k = len(infos) + 1
        lab[y, x] = k
        q = deque([(y, x)])
        n, y0, y1, x0, x1 = 0, y, y, x, x
        while q:
            cy, cx = q.popleft()
            n += 1
            y0, y1, x0, x1 = min(y0, cy), max(y1, cy), min(x0, cx), max(x1, cx)
            for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                if 0 <= ny < h and 0 <= nx < w and m[ny, nx] and not lab[ny, nx]:
                    lab[ny, nx] = k
                    q.append((ny, nx))
        infos.append((n, y0, y1, x0, x1))
    return lab, infos
