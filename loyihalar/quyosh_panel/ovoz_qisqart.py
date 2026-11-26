"""AI ovozdagi pauzalarni qisqartiradi (CLAUDE.md: kesish qoidalari).

Gap chegaralari: RMS 25 ms, -42 dB. Boshidan 0.05 s, oxiridan 0.08 s qoldiriladi.
Ichki pauza >=0.25 s -> 0.12 s; uzun pauza >=0.6 s (odatda xatboshi) -> 0.25 s.
Ulanishlarda 10 ms crossfade (chiqillamasligi uchun).
Ishlatish: python ovoz_qisqart.py kirish.wav chiqish.wav [vaqt_xarita.json]
"""
import json
import sys
import wave

import numpy as np

QADAM, CHEGARA_DB = 0.025, -42


def oqi(f):
    w = wave.open(f)
    sr = w.getframerate()
    return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768, sr


def yoz(f, x, sr):
    w = wave.open(f, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()


def bolaklar(x, sr):
    h = int(sr * QADAM); n = len(x) // h
    db = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)
    sp, seg, i = db > CHEGARA_DB, [], 0
    while i < n:
        if sp[i]:
            j = i
            while j < n and sp[j]:
                j += 1
            if seg and i * QADAM - seg[-1][1] < 0.1:
                seg[-1] = (seg[-1][0], j * QADAM)
            else:
                seg.append((i * QADAM, j * QADAM))
            i = j
        else:
            i += 1
    return seg


def qisqart(x, sr):
    seg = bolaklar(x, sr)
    # pauzalar: < 0.25 s o'zgarmaydi (bo'laklar birlashtiriladi)
    guruh = [list(seg[0])]
    pauza = []
    for a, b in seg[1:]:
        g = a - guruh[-1][1]
        if g < 0.25:
            guruh[-1][1] = b
        else:
            guruh.append([a, b]); pauza.append(0.25 if g >= 0.6 else 0.12)
    xf = int(sr * 0.01)
    chiq, xarita, t = np.zeros(0, np.float32), [], 0.0
    for k, (a, b) in enumerate(guruh):
        s0 = max(0, int((a - 0.05) * sr)); s1 = min(len(x), int((b + 0.08) * sr))
        bo = x[s0:s1].copy()
        if len(chiq) and xf:
            bo[:xf] *= np.linspace(0, 1, xf); chiq[-xf:] *= np.linspace(1, 0, xf)
            chiq = np.concatenate([chiq[:-xf], chiq[-xf:] + bo[:xf], bo[xf:]])
        else:
            chiq = bo
        xarita.append({"asl": [round(a, 3), round(b, 3)], "yangi_boshi": round(len(chiq) / sr - (s1 - s0) / sr + (a - s0 / sr) + (xf / sr if k else 0), 3)})
        if k < len(pauza):
            sukut = max(0.0, pauza[k] - 0.05 - 0.08)
            chiq = np.concatenate([chiq, np.zeros(int(sukut * sr), np.float32)])
    return chiq, xarita, pauza


if __name__ == "__main__":
    x, sr = oqi(sys.argv[1])
    y, xarita, pauza = qisqart(x, sr)
    yoz(sys.argv[2], y, sr)
    if len(sys.argv) > 3:
        json.dump({"bolaklar": xarita, "pauzalar": pauza}, open(sys.argv[3], "w"), ensure_ascii=False, indent=1)
    print(f"asl {len(x) / sr:.2f} s -> {len(y) / sr:.2f} s, bo'laklar {len(xarita)}, uzun pauza {pauza.count(0.25)}")
