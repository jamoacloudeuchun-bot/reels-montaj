"""Musiqa nomzodlarini ovoz bilan aralashtirib eshitish uchun preview (video render emas).

Montaj yadrosidagi qoidalar: musiqa -21 LUFS (bu loyihada -25, foydalanuvchi so'rovi), nutq ostida ducking (-6 dB), yakuniy -14 LUFS, TP -1.5.
Trekdagi drop asosiy momentga (\"uchta sabab\", ~7.1 s) to'g'rilanadi.
Ishlatish: python musiqa_sinov.py ovoz.wav musiqa.mp3|- drop_s chiqish.wav [moment_s] [vaqt_chizigi.json]
"""
import sys

import numpy as np

sys.path.insert(0, "/home/user/reels-montaj")
from montaj.ovoz_miks import SR, _oqi, lufs, normallashtir  # noqa: E402

DUM_S = 0.7          # ovoz tugagach musiqa davom etadigan vaqt
DUCK_DB = -6
MUSIQA_LUFS = -25    # foydalanuvchi: Carefree ovozini pasaytirish (-21 -> -25)
SFX_DB = -8          # SFX asosiy darajasi (cho'qqi -3 dBFS dan)
SFX_GAP_USTIDA_DB = -5  # CLAUDE.md: gap ustiga chiqqan SFX -5 dB


def nutq_maskasi(x, sr, qadam=0.025, chegara_db=-42):
    h = int(sr * qadam); n = len(x) // h
    db = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)
    m = (db > chegara_db).astype(float)
    k = 6  # 0.15 s silliqlash
    m = np.convolve(m, np.ones(k) / k, mode="same").clip(0, 1)
    r = np.repeat(m, h)
    return np.pad(r, (0, max(0, len(x) - len(r))), mode="edge")[:len(x)]


def aralashtir(ovoz_f, musiqa_f, drop_s, chiqish, moment_s=7.1, vaqt_chizigi=None):
    v = _oqi(ovoz_f, SR)
    n = len(v) + int(DUM_S * SR)
    v = np.pad(v, (0, n - len(v)))
    mk = nutq_maskasi(v, SR)
    boshi = None
    if musiqa_f == "-":                    # musiqasiz variant (foydalanuvchi qarori)
        m = np.zeros(n, np.float32)
    else:
        m = _oqi(musiqa_f, SR)
        boshi = max(0.0, drop_s - moment_s)
        m = m[int(boshi * SR):int(boshi * SR) + n]
        m = np.pad(m, (0, n - len(m)))
        m *= 10 ** ((MUSIQA_LUFS - lufs(m, SR)) / 20)
        m *= 10 ** (DUCK_DB * mk / 20)
        fi, fo = int(0.3 * SR), int(1.5 * SR)
        m[:fi] *= np.linspace(0, 1, fi); m[-fo:] *= np.linspace(1, 0, fo)
    x = v + m
    sfx_soni = 0
    if vaqt_chizigi:
        import json
        for h in json.load(open(vaqt_chizigi))["hodisalar"]:
            s = _oqi(f"kesh/sfx/{h['sfx']}.wav", SR)
            i = int(h["t"] * SR); s = s[:max(0, len(x) - i)]
            db = SFX_DB + (SFX_GAP_USTIDA_DB if mk[i:i + len(s)].max(initial=0) > 0.5 else 0)
            x[i:i + len(s)] += s * 10 ** (db / 20)
            sfx_soni += 1
    info = normallashtir(x, SR, chiqish)
    info["sfx"] = sfx_soni
    info.update(musiqa_boshi_s=None if boshi is None else round(boshi, 2), davomiylik_s=round(n / SR, 2))
    return info


if __name__ == "__main__":
    a = sys.argv
    print(aralashtir(a[1], a[2], float(a[3]), a[4], float(a[5]) if len(a) > 5 else 7.1,
                     a[6] if len(a) > 6 else None))
