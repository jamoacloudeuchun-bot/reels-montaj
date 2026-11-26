"""ChatGPT setka-rasmidan stikerlarni shaffof PNG qilib kesadi.

Fon: oq (>=246, past to'yinganlik), chetdan flood-fill. Stiker oq konturi
atrofidagi xira kulrang chiziq (uzilishlari yopilgan holda) to'ldirishni to'xtatadi,
shuning uchun oq kontur va ichki oq joylar (qo'lqop, krossovka) saqlanadi.
Ishlatish: python stiker_kes.py <rasm.png> <chiqish_papka> <prefiks> x0 y0 x1 y1
           python stiker_kes.py <rasm.png> <chiqish_papka> <prefiks> --setka 3x2
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def _kengay(m, r):
    for _ in range(r):
        n = m.copy()
        n[1:] |= m[:-1]; n[:-1] |= m[1:]; n[:, 1:] |= m[:, :-1]; n[:, :-1] |= m[:, 1:]
        m = n
    return m


def _toldir(ruxsat):
    """Chetdan 4-qo'shnili flood-fill, faqat `ruxsat` piksellar bo'ylab."""
    m = np.zeros_like(ruxsat)
    m[0, :], m[-1, :], m[:, 0], m[:, -1] = ruxsat[0, :], ruxsat[-1, :], ruxsat[:, 0], ruxsat[:, -1]
    while True:
        n = _kengay(m, 1) & ruxsat
        if (n == m).all():
            return m
        m = n


def fon_maska(a, yopish=6):
    """Oq fon maskasi. Stiker oq konturi atrofidagi xira kulrang chiziqda uzilishlar
    bo'lishi mumkin, shuning uchun to'siqni `yopish` px kengaytirib, fonni tashqaridan
    to'ldiramiz, keyin fonni shuncha px qaytaramiz (faqat oq piksellar bo'ylab)."""
    mx, mn = a.max(2), a.min(2)
    oq = (mn >= 246) & (mx - mn <= 6)
    tosiq = _kengay(~oq, yopish)
    fon = _toldir(~tosiq)
    for _ in range(yopish):
        fon = _kengay(fon, 1) & oq
    return fon


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


def _chegara(profil, n):
    """Setka katakchalari chegarasi: kutilgan joy atrofida (±15%) eng bo'sh ustun/qator."""
    L = len(profil); res = [0]
    for i in range(1, n):
        c, r = L * i // n, int(L * 0.15)
        res.append(c - r + int(np.argmin(profil[c - r:c + r])))
    return res + [L]


def setka_kes(rasm, chiqish, prefiks, ustun, qator):
    """Setkadagi stikerlarni kesadi. Qo'shni stikerlarning oq konturlari tegib
    turgan bo'lsa ham ajratadi: har katakdagi rangli "yadro" urug' bo'ladi va
    stiker maskasi bo'ylab eng yaqin urug'ga qarab bo'linadi."""
    Path(chiqish).mkdir(parents=True, exist_ok=True)
    a = np.asarray(Image.open(rasm).convert("RGB")).astype(int)
    obyekt = ~fon_maska(a)
    yadro = a.min(2) < 200
    belgi = np.zeros(yadro.shape, dtype=np.int32)
    ys = _chegara(yadro.sum(1), qator)
    k = 0
    for qi in range(qator):
        xs = _chegara(yadro[ys[qi]:ys[qi + 1]].sum(0), ustun)
        for ui in range(ustun):
            k += 1
            sl = (slice(ys[qi], ys[qi + 1]), slice(xs[ui], xs[ui + 1]))
            belgi[sl][yadro[sl] & obyekt[sl]] = k
    # urug'larni obyekt maskasi bo'ylab kengaytirish (ko'p manbali BFS)
    while True:
        bosh = (belgi == 0) & obyekt
        if not bosh.any():
            break
        yangi = belgi.copy()
        for sy, sx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            siljigan = np.roll(belgi, (sy, sx), axis=(0, 1))
            m = bosh & (yangi == 0) & (siljigan > 0)
            yangi[m] = siljigan[m]
        if (yangi == belgi).all():
            break  # yadrosiz qolgan obyekt bo'laklari (shovqin) tashlanadi
        belgi = yangi
    natija = []
    for n in range(1, k + 1):
        m = belgi == n
        yy, xx = np.nonzero(m)
        y0, y1, x0, x1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
        alfa = np.where(m[y0:y1, x0:x1], 255, 0)
        im = Image.fromarray(np.dstack([a[y0:y1, x0:x1], alfa]).astype(np.uint8), "RGBA")
        f = Path(chiqish) / f"{prefiks}_{n}.png"
        im.save(f)
        natija.append((f.name, im.size))
    return natija


if __name__ == "__main__":
    rasm, chiq, prefiks = sys.argv[1], sys.argv[2], sys.argv[3]
    if sys.argv[4] == "--setka":  # masalan: --setka 3x2 (ustun x qator)
        u, q = map(int, sys.argv[5].split("x"))
        print(setka_kes(rasm, chiq, prefiks, u, q))
    else:
        print(kes(rasm, chiq, tuple(map(int, sys.argv[4:8])), prefiks))
