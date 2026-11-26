"""Subtitr: matn tasdiqlangan ssenariydan (OVOZ_MATNI.txt), vaqtlar Whisper so'z vaqtlaridan.

CLAUDE.md: Whisper o'zbekchani yomon o'qiydi — undan faqat so'z vaqtlari olinadi; vaqtlar ovoz
energiyasi (RMS 25 ms, -42 dB) bo'yicha aniqlashtiriladi.
Ssenariy so'zlari Whisper so'zlariga harflar darajasida (normallashtirilgan) moslashtiriladi.

Ishlatish: python subtitr.py  ->  subtitr.json
"""
import difflib
import json
import re
import sys

import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from ovoz_qisqart import oqi  # noqa: E402

# boshqa loyihalar uchun: python subtitr.py [matn.txt] [sozlar_whisper.json] [ovoz.wav]  (joriy papkada)
MATN = sys.argv[1] if len(sys.argv) > 1 else "OVOZ_MATNI.txt"
WHISPER = sys.argv[2] if len(sys.argv) > 2 else "kesh/ovoz/sozlar_whisper.json"
OVOZ = sys.argv[3] if len(sys.argv) > 3 else "kesh/ovoz/ovoz_final.wav"
MAKS_SOZ, MAKS_HARF = 3, 20


def norm(s):
    s = s.lower().replace("‘", "").replace("'", "").replace("’", "")
    s = s.replace("q", "k").replace("x", "h").replace("ng", "n")
    return re.sub(r"[^a-z]", "", s)


def sozlar_vaqti():
    sc = [w for w in open(MATN, encoding="utf-8").read().split() if norm(w)]  # yolg'iz tire va h.k. tashlanadi
    wh = json.load(open(WHISPER))
    # harf -> whisper vaqti (har harfga so'z ichida chiziqli interpolatsiya)
    w_harf, w_t = [], []
    for w in wh:
        n = norm(w["w"])
        for i, ch in enumerate(n):
            w_harf.append(ch)
            w_t.append(w["a"] + (w["b"] - w["a"]) * i / max(1, len(n)))
    s_harf, s_soz = [], []
    for k, w in enumerate(sc):
        for ch in norm(w):
            s_harf.append(ch); s_soz.append(k)
    sm = difflib.SequenceMatcher(None, s_harf, w_harf, autojunk=False)
    t = [None] * len(s_harf)
    for a, b, n in sm.get_matching_blocks():
        for i in range(n):
            t[a + i] = w_t[b + i]
    # mos kelmagan harflar: qo'shnilar orasida interpolatsiya
    idx = [i for i, v in enumerate(t) if v is not None]
    t = list(np.interp(range(len(t)), idx, [t[i] for i in idx]))
    boshi = {}
    for i, k in enumerate(s_soz):
        boshi.setdefault(k, t[i])
    oxiri = {k: t[max(i for i, kk in enumerate(s_soz) if kk == k)] for k in boshi}
    return [(sc[k], boshi[k], oxiri[k]) for k in range(len(sc))], sm.ratio()


def rms_onsetlar():
    x, sr = oqi(OVOZ)
    h = int(sr * 0.025); n = len(x) // h
    db = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)
    gap = db > -42
    return [i * 0.025 for i in range(1, n) if gap[i] and not gap[i - 1]]


def bolaklar(sozlar):
    res, joriy = [], []
    for w, a, b in sozlar:
        joriy.append((w, a, b))
        matn = " ".join(x[0] for x in joriy)
        if len(joriy) >= MAKS_SOZ or len(matn) >= MAKS_HARF or re.search(r"[.,!?:]$", w):
            res.append(joriy); joriy = []
    if joriy:
        res.append(joriy)
    return res


if __name__ == "__main__":
    sozlar, moslik = sozlar_vaqti()
    ons = rms_onsetlar()
    chiq = []
    for b in bolaklar(sozlar):
        a = b[0][1]
        # pauzadan keyingi bo'lak: boshini RMS bo'yicha haqiqiy gap boshiga to'g'rilash (±0.25 s)
        yaqin = [o for o in ons if abs(o - a) <= 0.25]
        if yaqin:
            a = min(yaqin, key=lambda o: abs(o - a))
        chiq.append({"matn": " ".join(x[0] for x in b).rstrip(",:"), "a": round(a, 3), "b": round(b[-1][2], 3),
                     # karaoke uchun so'z boshlari (Whisper, bo'lak boshi RMS bo'yicha tuzatilgan)
                     "sozlar": [round(max(a, x[1]), 3) for x in b]})
    for i in range(len(chiq) - 1):        # keyingi bo'lakkacha ushlab turish (0.4 s dan kichik oraliq)
        if chiq[i + 1]["a"] - chiq[i]["b"] < 0.4:
            chiq[i]["b"] = chiq[i + 1]["a"]
        else:
            chiq[i]["b"] = round(chiq[i]["b"] + 0.2, 3)
    chiq[-1]["b"] = round(chiq[-1]["b"] + 0.3, 3)
    json.dump(chiq, open("subtitr.json", "w"), ensure_ascii=False, indent=1)
    print(f"moslik {moslik:.2f}, bo'laklar {len(chiq)}")
    for c in chiq:
        print(f"{c['a']:6.2f}-{c['b']:6.2f}  {c['matn']}")
