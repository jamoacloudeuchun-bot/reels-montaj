"""ChatGPT setka-rasmidan stikerlarni shaffof PNG qilib kesadi.

Fon: oq (>=246, past to'yinganlik), chetdan flood-fill. Stiker oq konturi
atrofidagi xira kulrang chiziq to'ldirishni to'xtatadi, shuning uchun oq kontur saqlanadi.
Ishlatish: python stiker_kes.py <rasm.png> <chiqish_papka> <prefiks> x0 y0 x1 y1
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def fon_maska(a):
    mx, mn = a.max(2), a.min(2)
    oq = (mn >= 246) & (mx - mn <= 6)
    m = np.zeros_like(oq)
    m[0, :], m[-1, :], m[:, 0], m[:, -1] = oq[0, :], oq[-1, :], oq[:, 0], oq[:, -1]
    while True:  # 4-qo'shnili flood-fill (dilatsiya bilan)
        n = m.copy()
        n[1:] |= m[:-1]; n[:-1] |= m[1:]; n[:, 1:] |= m[:, :-1]; n[:, :-1] |= m[:, 1:]
        n &= oq
        if (n == m).all():
            return m
        m = n


def komponentlar(ob, min_maydon=2000):
    """8-qo'shnili bog'langan komponentlar: [(y0, y1, x0, x1, maska), ...]."""
    from collections import deque
    h, w = ob.shape
    belgi = np.zeros((h, w), dtype=np.int32)
    res = []
    for sy, sx in zip(*np.nonzero(ob)):
        if belgi[sy, sx]:
            continue
        k = len(res) + 1
        q = deque([(sy, sx)]); belgi[sy, sx] = k
        nuqtalar = []
        while q:
            y, x = q.popleft(); nuqtalar.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and ob[ny, nx] and not belgi[ny, nx]:
                        belgi[ny, nx] = k; q.append((ny, nx))
        ys, xs = np.array(nuqtalar).T
        res.append((ys.min(), ys.max() + 1, xs.min(), xs.max() + 1, k, len(nuqtalar)))
    return belgi, [r for r in res if r[5] >= min_maydon]


def kes(rasm, chiqish, mintaqa, prefiks):
    Path(chiqish).mkdir(parents=True, exist_ok=True)
    a = np.asarray(Image.open(rasm).convert("RGB"))[mintaqa[1]:mintaqa[3], mintaqa[0]:mintaqa[2]].astype(int)
    fon = fon_maska(a)
    belgi, komp = komponentlar(~fon)
    # 2 qatorli setka: avval qator (markaz balandlikning yarmidan pastmi), keyin chapdan o'ngga
    h = a.shape[0]
    komp.sort(key=lambda r: ((r[0] + r[1]) / 2 >= h / 2, r[2]))
    natija = []
    for n, (y0, y1, x0, x1, k, _) in enumerate(komp, 1):
        alfa = np.where(belgi[y0:y1, x0:x1] == k, 255, 0)
        rgba = np.dstack([a[y0:y1, x0:x1], alfa]).astype(np.uint8)
        im = Image.fromarray(rgba, "RGBA")
        f = Path(chiqish) / f"{prefiks}_{n}.png"
        im.save(f)
        natija.append((f.name, im.size))
    return natija


if __name__ == "__main__":
    rasm, chiq, prefiks = sys.argv[1], sys.argv[2], sys.argv[3]
    print(kes(rasm, chiq, tuple(map(int, sys.argv[4:8])), prefiks))
