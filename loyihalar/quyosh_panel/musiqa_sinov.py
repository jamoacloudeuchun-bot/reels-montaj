"""Musiqa nomzodlarini ovoz bilan aralashtirib eshitish uchun preview (video render emas).

Montaj yadrosidagi qoidalar: musiqa -21 LUFS, nutq ostida ducking (-6 dB), yakuniy -14 LUFS, TP -1.5.
Trekdagi drop asosiy momentga (\"uchta sabab\", ~7.1 s) to'g'rilanadi.
Ishlatish: python musiqa_sinov.py ovoz.wav musiqa.mp3 drop_s chiqish.wav [moment_s]
"""
import sys

import numpy as np

sys.path.insert(0, "/home/user/reels-montaj")
from montaj.ovoz_miks import SR, _oqi, lufs, normallashtir  # noqa: E402

DUM_S = 0.7          # ovoz tugagach musiqa davom etadigan vaqt
DUCK_DB = -6


def nutq_maskasi(x, sr, qadam=0.025, chegara_db=-42):
    h = int(sr * qadam); n = len(x) // h
    db = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)
    m = (db > chegara_db).astype(float)
    k = 6  # 0.15 s silliqlash
    m = np.convolve(m, np.ones(k) / k, mode="same").clip(0, 1)
    r = np.repeat(m, h)
    return np.pad(r, (0, max(0, len(x) - len(r))), mode="edge")[:len(x)]


def aralashtir(ovoz_f, musiqa_f, drop_s, chiqish, moment_s=7.1):
    v = _oqi(ovoz_f, SR)
    n = len(v) + int(DUM_S * SR)
    v = np.pad(v, (0, n - len(v)))
    m = _oqi(musiqa_f, SR)
    boshi = max(0.0, drop_s - moment_s)
    m = m[int(boshi * SR):int(boshi * SR) + n]
    m = np.pad(m, (0, n - len(m)))
    m *= 10 ** ((-21 - lufs(m, SR)) / 20)
    mk = nutq_maskasi(v, SR)
    m *= 10 ** (DUCK_DB * mk / 20)
    fi, fo = int(0.3 * SR), int(1.5 * SR)
    m[:fi] *= np.linspace(0, 1, fi); m[-fo:] *= np.linspace(1, 0, fo)
    info = normallashtir(v + m, SR, chiqish)
    info.update(musiqa_boshi_s=round(boshi, 2), davomiylik_s=round(n / SR, 2))
    return info


if __name__ == "__main__":
    a = sys.argv
    print(aralashtir(a[1], a[2], float(a[3]), a[4], float(a[5]) if len(a) > 5 else 7.1))
