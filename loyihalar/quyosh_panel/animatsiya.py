"""Quyosh paneli reels: stiker animatsiyasi (kamerasiz), v2.

v2 o'zgarishlari (foydalanuvchi so'rovi):
- Quyoshvoy pastda, "yerda" turadi va gapirayotgandek qimirlaydi (ovoz energiyasiga bog'liq
  chayqalish, siqilish-cho'zilish, tebranish). Buyumlar tepada.
- Subtitr (matn — tasdiqlangan ssenariy, vaqt — Whisper + RMS), oq, tepada.
- Stikerlar soyasiz (stiker_tozala.py), 4K (2160x3840) 60 fps.

CLAUDE.md: kirish pop 80→106→100% (0.3 s); matn pastdan ~36 px ko'tarilib 0.2 s fade; chiqish 0.25 s fade;
safe zona x 150–930 (yon elementlar x≈80 dan), y 230–1595 (1080x1920 koordinatalarida); matn oq, soyasiz.
Barcha koordinatalar 1080x1920 tizimida yoziladi va S marta kattalashtiriladi.

Ishlatish:
  python animatsiya.py kadr 3.0 11.5 20.9 27.6          # sinov kadrlari (render emas)
  python animatsiya.py render --tasdiq --audio A.wav --chiqish V.mp4
"""
import json
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

S = 2                      # 1 -> 1080x1920, 2 -> 4K 2160x3840
W, H, FPS = 1080 * S, 1920 * S, 60
DAVOMIYLIK = 39.98
ASL = Path("asl/chatgpt_v1_umumiy.png")
ST_BUYUM = Path("stikerlar/buyum")
ST_PERSONAJ = Path("stikerlar/personaj_toza")
OVOZ = Path("kesh/ovoz/ovoz_final.wav")
SUBTITR = Path("subtitr.json")
SHRIFT = "/home/user/reels-montaj/shriftlar/Oswald/Oswald-VariableFont_wght.ttf"

POP_S, KIRISH_FADE_S, CHIQISH_S = 0.30, 0.10, 0.25

# sahnalar (Whisper so'z vaqtlari bo'yicha): (boshi, oxiri, fon)
SAHNALAR = [
    (0.00, 5.20, "kun"),     # hook
    (5.20, 9.35, "kun"),     # salom, 3 sabab
    (9.35, 16.35, "kun"),    # 1-sabab
    (16.35, 22.80, "tun"),   # 2-sabab
    (22.80, 30.05, "kun"),   # 3-sabab
    (30.05, 34.10, "kun"),   # xulosa
    (34.10, DAVOMIYLIK, "kun"),  # CTA
]

# Quyoshvoy: yerda (oyoqlari y=1580), markazda; poza almashganda pop
PERSONAJ_OYOQ = (540, 1580)
PERSONAJ_H = 520
POZALAR = [(2.05, "personaj_1"), (9.40, "personaj_2"), (16.40, "personaj_6"),
           (22.85, "personaj_3"), (30.10, "personaj_5"), (34.15, "personaj_2")]


def E(sahna, nom, t0, cx, cy, h, **kw):
    return dict(sahna=sahna, nom=nom, t0=t0, cx=cx, cy=cy, h=h, **kw)


# buyumlar tepada: y 480–1000 oralig'i (subtitr ~y 330, personaj y 1060–1580)
ELEMENTLAR = [
    # 1 — hook: uy, pul uchib ketadi ("pul to'laysiz")
    E(1, "buyum_1", 0.10, 540, 760, 440),
    E(1, "buyum_7", 1.20, 540, 760, 170, yol=((540, 760), (230, 500), 0.8), yoqol=2.2),
    E(1, "buyum_7", 1.75, 540, 760, 170, yol=((540, 760), (850, 500), 0.8), yoqol=2.75),
    # 2 — "Quyosh panelini" + "uchta sabab" ikonkalari (raqamsiz)
    E(2, "buyum_2", 7.35, 540, 600, 260),
    E(2, "buyum_7", 8.46, 260, 920, 150),
    E(2, "buyum_5", 8.72, 540, 920, 180),
    E(2, "buyum_8", 8.98, 820, 920, 160),
    # 3 — 1-sabab: panel tomga tushadi ("Kunduzi"), pul kichrayadi ("kichrayadi")
    E(3, "buyum_1", 9.45, 540, 780, 460),
    E(3, "buyum_2", 11.16, 560, 525, 160, yol=((560, 250), (560, 525), 0.30), kirish="tush"),
    E(3, "buyum_7", 14.38, 860, 950, 180, kichray=(15.74, 0.5)),
    # 4 — 2-sabab, tun: jihozlar so'z bilan birga
    E(4, "buyum_3", 19.10, 540, 720, 400),
    E(4, "buyum_4", 20.04, 230, 800, 330),
    E(4, "buyum_5", 20.86, 850, 560, 200),
    E(4, "buyum_6", 21.42, 850, 930, 170),
    # 5 — 3-sabab: kopilka ("sarmoya"), panel ("Panel"), tangalar tushadi
    E(5, "buyum_8", 24.72, 610, 860, 330),
    E(5, "buyum_2", 25.36, 250, 560, 240),
    E(5, "buyum_7", 27.08, 280, 660, 100, yol=((280, 660), (600, 790), 0.35), yoqol=27.48, kirish="tush"),
    E(5, "buyum_7", 27.62, 280, 660, 100, yol=((280, 660), (600, 790), 0.35), yoqol=28.02, kirish="tush"),
    E(5, "buyum_7", 28.42, 280, 660, 100, yol=((280, 660), (600, 790), 0.35), yoqol=28.82, kirish="tush"),
    # 6 — xulosa: quyosh nuri (panel) yuqorida
    E(6, "buyum_2", 30.62, 540, 700, 300),
    # 7 — CTA: personaj pastga ko'rsatadi (buyumsiz)
]


# ---------------- yordamchilar ----------------

def _ease_out(u):
    return 1 - (1 - u) ** 3


def pop_masshtab(u):
    if u <= 0:
        return 0.80
    if u < 0.55:
        return 0.80 + 0.26 * _ease_out(u / 0.55)
    if u < 1:
        return 1.06 - 0.06 * _ease_out((u - 0.55) / 0.45)
    return 1.0


@lru_cache(maxsize=None)
def fon(qaysi):
    asl = Image.open(ASL).convert("RGB")
    box = (209, 608, 606, 1229) if qaysi == "kun" else (649, 609, 1046, 1229)
    f = asl.crop(box)
    k = H / f.height
    f = f.resize((round(f.width * k), H), Image.LANCZOS)
    x = (f.width - W) // 2
    return f.crop((x, 0, x + W, H)).convert("RGBA")


@lru_cache(maxsize=None)
def _asl(nom):
    papka = ST_PERSONAJ if nom.startswith("personaj") else ST_BUYUM
    return Image.open(papka / f"{nom}.png").convert("RGBA")


@lru_cache(maxsize=512)
def stiker(nom, h):
    s = _asl(nom)
    return s.resize((max(1, round(s.width * h / s.height)), h), Image.LANCZOS)


def _alfa(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    return im


@lru_cache(maxsize=1)
def ovoz_energiyasi():
    """Ovoz energiyasi 0..1 (10 ms qadam), hujum 30 ms / qaytish 120 ms bilan silliqlangan."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(OVOZ), "-ac", "1", "-ar", "48000", "-f", "f32le", "-"],
                       capture_output=True, check=True)
    x = np.frombuffer(r.stdout, np.float32)
    h = 480
    n = len(x) // h
    rms = np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1))
    db = 20 * np.log10(rms + 1e-9)
    e = np.clip((db + 42) / 24, 0, 1)            # -42 dB -> 0, -18 dB -> 1
    out = np.zeros_like(e)
    for i in range(1, n):
        k = 0.28 if e[i] > out[i - 1] else 0.08
        out[i] = out[i - 1] + k * (e[i] - out[i - 1])
    return out


def energiya(t):
    e = ovoz_energiyasi()
    i = int(t * 100)
    return float(e[i]) if 0 <= i < len(e) else 0.0


# ---------------- elementlar ----------------

def sahna_raqami(t):
    for i, (a, b, _) in enumerate(SAHNALAR, 1):
        if a <= t < b:
            return i
    return len(SAHNALAR)


def element_holati(e, t):
    s0, s1, _ = SAHNALAR[e["sahna"] - 1]
    if t < e["t0"] or t >= s1:
        return None
    u = t - e["t0"]
    cx, cy, m = e["cx"], e["cy"], 1.0
    if "yol" in e:
        (x0, y0), (x1, y1), d = e["yol"]
        k = min(1.0, u / d) ** 2 if e.get("kirish") == "tush" else _ease_out(min(1.0, u / d))
        cx, cy = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    a = min(1.0, u / KIRISH_FADE_S)
    if e.get("kirish") != "tush":
        m = pop_masshtab(u / POP_S)
    if "yoqol" in e:
        if t >= e["yoqol"]:
            return None
        a *= min(1.0, (e["yoqol"] - t) / 0.2)
    if "kichray" in e and t >= e["kichray"][0]:
        tk, oxir = e["kichray"]
        m *= 1 - (1 - oxir) * _ease_out(min(1.0, (t - tk) / 0.3))
    if u > POP_S and e.get("kirish") != "tush" and "yol" not in e:   # buyumlar ham yengil "nafas oladi"
        cy += 4 * math.sin(2 * math.pi * (u - POP_S) / 2.2 + e["t0"])
    if t > s1 - CHIQISH_S:
        a *= max(0.0, (s1 - t) / CHIQISH_S)
    return cx, cy, m, a


def personaj(im, t):
    """Quyoshvoy: oyoqlari yerda, gapirganda qimirlaydi."""
    if t < POZALAR[0][0]:
        return
    joriy = max((p for p in POZALAR if p[0] <= t), key=lambda p: p[0])
    u = t - joriy[0]
    e = energiya(t)
    m = pop_masshtab(u / POP_S)
    a = min(1.0, (t - POZALAR[0][0]) / KIRISH_FADE_S)
    sy = m * (1 + 0.045 * e)                    # gapirganda biroz cho'ziladi
    sx = m * (1 - 0.025 * e)
    burchak = 3.0 * math.sin(2 * math.pi * t / 1.15) * (0.35 + 0.65 * e)   # chayqalish
    burchak += 1.2 * math.sin(2 * math.pi * t / 0.37) * e                 # gap ritmi
    kotar = 14 * e                              # gapirganda biroz ko'tariladi
    if joriy[1] == "personaj_5":               # xursand sakrash
        kotar += 60 * abs(math.sin(math.pi * u / 0.55))
    s = _asl(joriy[1])
    hh = round(PERSONAJ_H * S * sy)
    ww = round(s.width * PERSONAJ_H * S / s.height * sx)
    st = s.resize((max(1, ww), max(1, hh)), Image.BICUBIC)
    st = _alfa(st, a)
    # oyoq nuqtasi atrofida aylantirish: rasm markazidan aylantirib, oyoq siljishini qoplaymiz
    r = st.rotate(burchak, resample=Image.BICUBIC, expand=True)
    rad = math.radians(burchak)
    dx, dy = 0, st.height / 2                   # markazdan oyoqqacha vektor
    rx = dx * math.cos(rad) + dy * math.sin(rad)
    ry = -dx * math.sin(rad) + dy * math.cos(rad)
    fx, fy = PERSONAJ_OYOQ[0] * S, (PERSONAJ_OYOQ[1] - kotar) * S
    im.alpha_composite(r, (round(fx - rx - r.width / 2), round(fy - ry - r.height / 2)))


# ---------------- subtitr ----------------

@lru_cache(maxsize=1)
def subtitrlar():
    return json.load(open(SUBTITR))


@lru_cache(maxsize=8)
def shrift(o):
    f = ImageFont.truetype(SHRIFT, o)
    try:
        f.set_variation_by_axes([600])
    except Exception:
        pass
    return f


@lru_cache(maxsize=64)
def subtitr_rasm(matn):
    o = 66 * S
    f = shrift(o)
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    l, tt, r, b = d.textbbox((0, 0), matn, font=f)
    while r - l > (720 - 70) * S:
        o -= 2 * S; f = shrift(o); l, tt, r, b = d.textbbox((0, 0), matn, font=f)
    pw, ph = 36 * S, 22 * S
    im = Image.new("RGBA", (r - l + 2 * pw, b - tt + 2 * ph), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=26 * S, fill=(12, 18, 48, 175))
    dd.text((pw - l, ph - tt), matn, font=f, fill=(255, 255, 255, 255))
    return im


def subtitr(im, t):
    for i, c in enumerate(subtitrlar()):
        if c["a"] <= t < c["b"]:
            u = t - c["a"]
            oldingi = subtitrlar()[i - 1] if i else None
            ulangan = oldingi and abs(oldingi["b"] - c["a"]) < 0.01
            # birinchi bo'lak (pauzadan keyin): pastdan 36 px ko'tarilib 0.2 s fade; ketma-ket bo'laklarda 0.08 s
            d = 0.08 if ulangan else 0.2
            k = _ease_out(min(1.0, u / d))
            a = k
            keyingi = subtitrlar()[i + 1] if i + 1 < len(subtitrlar()) else None
            if not (keyingi and abs(keyingi["a"] - c["b"]) < 0.01):
                a *= min(1.0, (c["b"] - t) / 0.2)       # pauza oldidan 0.2 s fade
            s = _alfa(subtitr_rasm(c["matn"]), a)
            cy = 330 * S + (1 - k) * (36 if not ulangan else 12) * S
            im.alpha_composite(s, (round(W / 2 - s.width / 2), round(cy - s.height / 2)))
            return


# ---------------- kadr ----------------

def kadr(t):
    n = sahna_raqami(t)
    s0, _, f = SAHNALAR[n - 1]
    im = fon(f).copy()
    if n > 1 and SAHNALAR[n - 2][2] != f and t - s0 < 0.3:
        im = Image.blend(fon(SAHNALAR[n - 2][2]), im, (t - s0) / 0.3)
    for e in ELEMENTLAR:
        if e["sahna"] != n:
            continue
        h = element_holati(e, t)
        if h is None:
            continue
        cx, cy, m, a = h
        s = _alfa(stiker(e["nom"], max(2, round(e["h"] * m * S))), a)
        im.alpha_composite(s, (round(cx * S - s.width / 2), round(cy * S - s.height / 2)))
    personaj(im, t)
    subtitr(im, t)
    if t > DAVOMIYLIK - CHIQISH_S:
        im = Image.blend(Image.new("RGBA", im.size, (0, 0, 0, 255)), im, max(0.0, (DAVOMIYLIK - t) / CHIQISH_S))
    return im.convert("RGB")


def safe_zona_tekshir():
    xato = []
    for e in ELEMENTLAR:
        s = stiker(e["nom"], e["h"] * S)
        pts = [(e["cx"], e["cy"])] + ([e["yol"][1]] if "yol" in e else [])
        for cx, cy in pts:
            x0, x1 = cx - s.width / S / 2, cx + s.width / S / 2
            y0, y1 = cy - s.height / S / 2 - 6, cy + s.height / S / 2 + 6
            if x0 < 80 or x1 > 1000 or y0 < 230 or y1 > 1595:
                xato.append((e["nom"], e["t0"], round(x0), round(y0), round(x1), round(y1)))
    for _, p in POZALAR:                       # personaj (maks. cho'zilish 1.06*1.045)
        s = _asl(p)
        hh = PERSONAJ_H * 1.06 * 1.045
        ww = s.width * PERSONAJ_H / s.height * 1.06
        if PERSONAJ_OYOQ[1] - hh - 60 < 230 or PERSONAJ_OYOQ[0] - ww / 2 < 80 or PERSONAJ_OYOQ[0] + ww / 2 > 1000:
            xato.append((p, "personaj"))
    for c in subtitrlar():
        s = subtitr_rasm(c["matn"])
        if s.width / S > 780 or 330 - s.height / S / 2 < 230:
            xato.append(("subtitr", c["matn"], s.width / S))
    return xato


if __name__ == "__main__":
    buyruq = sys.argv[1]
    if buyruq == "kadr":
        out = Path("kesh/anim_kadr_v2"); out.mkdir(parents=True, exist_ok=True)
        for v in map(float, sys.argv[2:]):
            kadr(v).save(out / f"t{v:05.2f}.png")
            print(out / f"t{v:05.2f}.png")
        print("safe zona xatolari:", safe_zona_tekshir())
    elif buyruq == "render":
        if "--tasdiq" not in sys.argv:
            sys.exit("TO'XTATILDI: render faqat foydalanuvchi tasdig'idan keyin (--tasdiq).")
        audio, chiq = sys.argv[sys.argv.index("--audio") + 1], sys.argv[sys.argv.index("--chiqish") + 1]
        n = round(DAVOMIYLIK * FPS)
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", audio,
                              "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
                              "-profile:v", "high", "-level", "5.2",
                              "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", chiq],
                             stdin=subprocess.PIPE)
        for i in range(n):
            p.stdin.write(kadr(i / FPS).tobytes())
            if i % 300 == 0:
                print(f"{i}/{n}", flush=True)
        p.stdin.close()
        sys.exit(p.wait())
