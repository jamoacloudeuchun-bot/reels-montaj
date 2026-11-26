"""Yozib olingan SFX fayldan alohida zarbalarni (pop, hit, whoosh) kesib oladi.

Hodisa: RMS (5 ms) chegaradan oshgan joy; boshidan 5 ms oldin, oxiri -45 dB gacha (maks. uzunlik bilan).
Ishlatish: python sfx_ajrat.py kirish.mp3 chiqish_prefiks maks_s [nechta]
"""
import sys

import numpy as np

sys.path.insert(0, "/home/user/reels-montaj")
from montaj.ovoz_miks import SR, _oqi  # noqa: E402

sys.path.insert(0, ".")
from ovoz_qisqart import yoz  # noqa: E402


def hodisalar(x, maks_s, qadam=0.005):
    h = int(SR * qadam); n = len(x) // h
    db = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)
    tepa = db.max()
    chegara = max(tepa - 30, -50)  # hodisa boshi
    res, i = [], 0
    while i < n:
        if db[i] > chegara:
            j = i
            while j < n and db[j] > tepa - 45 and (j - i) * qadam < maks_s:
                j += 1
            j = min(n, j + int(0.03 / qadam))  # tabiiy so'nish uchun 30 ms qo'shimcha
            res.append((max(0, i - 1) * h, j * h, float(db[i:j].max())))
            i = j + int(0.08 / qadam)
        else:
            i += 1
    return res


if __name__ == "__main__":
    f, pref, maks = sys.argv[1], sys.argv[2], float(sys.argv[3])
    nechta = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    x = _oqi(f, SR)
    hs = sorted(hodisalar(x, maks), key=lambda t: -t[2])[:nechta]
    for k, (a, b, p) in enumerate(sorted(hs), 1):
        s = x[a:b].copy()
        s /= max(1e-6, np.abs(s).max()) / 0.7          # cho'qqi -3 dBFS
        fo = min(len(s), int(0.02 * SR)); s[-fo:] *= np.linspace(1, 0, fo)
        yoz(f"{pref}_{k}.wav", s, SR)
        print(f"{pref}_{k}.wav  {a / SR:.2f}s  {len(s) / SR:.2f}s  {p:.1f} dB")
