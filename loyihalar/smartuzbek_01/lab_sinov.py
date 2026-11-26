"""Og'iz harakati (lip-sync) sinovi: asl og'iz o'chiriladi, o'rniga og'iz shakllari (vizemlar) qo'yiladi.

Bu SINOV: og'izlar dastur bilan chiziladi (vektor uslubida). ChatGPT'dan og'iz varag'i kelsa,
chizilgan og'izlar o'rniga o'sha rasmlar qo'yiladi — qolgan mantiq o'zgarmaydi.
Vizem tanlash: ovoz energiyasi (RMS) + so'zdagi unli harf (Whisper so'z vaqtlari).
"""
import json
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

TERI = (253, 197, 146)
KONTUR = (6, 14, 36)
ICH = (110, 28, 40)
TISH = (255, 255, 255)
TIL = (240, 120, 120)
OGIZ_MARKAZ = (198, 198)        # jurnalist_v0.png koordinatalari
OGIZ_QUTI = (164, 180, 232, 216)  # o'chiriladigan maydon


def ogizsiz(im):
    im = im.copy()
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = OGIZ_QUTI
    d.ellipse((x0, y0, x1, y1), fill=TERI + (255,))
    return im


def ogiz(shakl, k=1.0, ss=4):
    """Vizem rasmi (RGBA), markazi rasm markazida. shakl: X, M, kichik, A, E, O."""
    W, H = 90 * ss, 60 * ss
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = W // 2, H // 2
    lw = 3 * ss
    if shakl == "X":       # yopiq tabassum
        d.arc((cx - 26 * ss, cy - 20 * ss, cx + 26 * ss, cy + 8 * ss), 20, 160, fill=KONTUR, width=lw)
    elif shakl == "M":     # lablar qisilgan
        d.line((cx - 18 * ss, cy, cx + 18 * ss, cy), fill=KONTUR, width=lw)
    else:
        w, h = {"kichik": (20, 9), "A": (28, 22), "E": (30, 13), "O": (14, 18)}[shakl]
        w, h = w * ss, h * ss
        box = (cx - w, cy - h * 0.35, cx + w, cy + h)
        if shakl == "O":
            box = (cx - w, cy - h * 0.7, cx + w, cy + h * 0.9)
            d.ellipse(box, fill=ICH, outline=KONTUR, width=lw)
            d.ellipse((cx - w * 0.6, cy + h * 0.2, cx + w * 0.6, cy + h * 0.85), fill=TIL)
            d.ellipse(box, outline=KONTUR, width=lw)
        else:
            # "D" shakli: tepasi tekis, pasti yumaloq (asl og'iz uslubi)
            d.chord((box[0], box[1] - (box[3] - box[1]), box[2], box[3]), 0, 180, fill=ICH, outline=KONTUR, width=lw)
            if shakl in ("A", "E"):
                d.rectangle((box[0] + lw, box[1] + lw * 0.4, box[2] - lw, box[1] + h * 0.28), fill=TISH)
            if shakl in ("A", "kichik"):
                d.chord((cx - w * 0.55, cy + h * 0.25, cx + w * 0.55, cy + h * 1.3), 180, 360, fill=TIL)
            d.chord((box[0], box[1] - (box[3] - box[1]), box[2], box[3]), 0, 180, outline=KONTUR, width=lw)
    return im.resize((round(W / ss * k), round(H / ss * k)), Image.LANCZOS)


UNLI = {"a": "A", "e": "E", "i": "E", "o": "O", "u": "O", "ō": "O"}


def vizem_chizigi(ovoz_wav, sozlar_json, fps):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", ovoz_wav, "-ac", "1", "-ar", "48000", "-f", "f32le", "-"],
                       capture_output=True, check=True)
    x = np.frombuffer(r.stdout, np.float32)
    h = 48000 // fps
    n = len(x) // h
    db = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)
    e = np.clip((db + 42) / 22, 0, 1)
    sozlar = json.load(open(sozlar_json))
    res = []
    for i in range(n):
        t = i / fps
        if e[i] < 0.12:
            res.append("X"); continue
        soz = next((s for s in sozlar if s["a"] <= t <= s["b"]), None)
        unli = "A"
        if soz:
            harflar = [c for c in soz["w"].lower() if c in UNLI]
            if harflar:
                u = (t - soz["a"]) / max(0.05, soz["b"] - soz["a"])
                unli = UNLI[harflar[min(len(harflar) - 1, int(u * len(harflar)))]]
            if soz["w"].lower()[:1] in "mbp" and t - soz["a"] < 0.06:
                res.append("M"); continue
        res.append("kichik" if e[i] < 0.4 else unli)
    # titramaslik uchun: har shakl kamida 2 kadr tursin
    for i in range(1, len(res) - 1):
        if res[i] != res[i - 1] and res[i] != res[i + 1]:
            res[i] = res[i - 1]
    return res


if __name__ == "__main__":
    asos = Image.open("stikerlar/jurnalist_v0.png").convert("RGBA")
    bosh = ogizsiz(asos)
    if sys.argv[1] == "varaq":
        shakllar = ["X", "M", "kichik", "E", "A", "O"]
        sc = 2
        out = Image.new("RGBA", (len(shakllar) * 200 * sc // 2 + 20, 200 * sc // 2 + 20), (30, 40, 90, 255))
        for i, sh in enumerate(shakllar):
            f = bosh.copy()
            m = ogiz(sh)
            f.alpha_composite(m, (OGIZ_MARKAZ[0] - m.width // 2, OGIZ_MARKAZ[1] - m.height // 2))
            yuz = f.crop((110, 60, 290, 240)).resize((200, 200), Image.LANCZOS)
            out.alpha_composite(yuz, (10 + i * 200, 10))
        out.convert("RGB").save("korik/ogiz_shakllari_sinov.png")
    elif sys.argv[1] == "video":
        ovoz, sozlar, chiq, dur = sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5])
        fps = 30
        viz = vizem_chizigi(ovoz, sozlar, fps)
        cache = {}
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "720x720",
                              "-r", str(fps), "-i", "-", "-t", str(dur), "-i", ovoz, "-c:v", "libx264", "-pix_fmt",
                              "yuv420p", "-c:a", "aac", "-shortest", chiq], stdin=subprocess.PIPE)
        for i in range(int(dur * fps)):
            sh = viz[i] if i < len(viz) else "X"
            if sh not in cache:
                f = Image.new("RGBA", asos.size, (40, 120, 220, 255))
                f.alpha_composite(bosh)
                m = ogiz(sh)
                f.alpha_composite(m, (OGIZ_MARKAZ[0] - m.width // 2, OGIZ_MARKAZ[1] - m.height // 2))
                cache[sh] = f.crop((20, 0, 380, 360)).resize((720, 720), Image.LANCZOS).convert("RGB")
            p.stdin.write(cache[sh].tobytes())
        p.stdin.close(); p.wait()
