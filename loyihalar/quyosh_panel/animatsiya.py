"""Quyosh paneli reels: stiker animatsiyasi (kamerasiz).

CLAUDE.md qoidalari:
- Kirish: pop 80→106→100% (0.3 s) + qisqa fade. Chiqish: 0.25 s fade.
- Hamma narsa safe zonada (x 150–930, y 230–1595); yon elementlar x≈80 dan boshlanishi mumkin.
- Videoda yozuv va raqam yo'q (foydalanuvchi qarori). Shape layer'da blur/soya yo'q.
Vaqtlar `vaqt_chizigi.json` dagi SFX hodisalari bilan bir xil (SFX faqat grafikaga).

Ishlatish:
  python animatsiya.py kadr 3.2 11.2 20.6 27.3     # sinov kadrlari (render emas)
  python animatsiya.py render --tasdiq             # yakuniy video (faqat tasdiqdan keyin)
"""
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image

W, H, FPS = 1080, 1920, 30
DAVOMIYLIK = 39.98
ASL = Path("asl/chatgpt_v1_umumiy.png")
ST_BUYUM = Path("kesh/stiker")
ST_PERSONAJ = Path("stikerlar/personaj")

POP_S, KIRISH_FADE_S, CHIQISH_S = 0.30, 0.10, 0.25

# sahnalar: (boshi, oxiri, fon)
SAHNALAR = [
    (0.00, 5.85, "kun"),
    (5.85, 9.40, "kun"),
    (9.40, 16.45, "kun"),
    (16.45, 22.90, "tun"),
    (22.90, 30.20, "kun"),
    (30.20, 33.55, "kun"),
    (33.55, DAVOMIYLIK, "kun"),
]


def E(sahna, nom, t0, cx, cy, h, **kw):
    """Element: sahna raqami (1..7), stiker nomi, paydo bo'lish vaqti, markaz va balandlik (px)."""
    return dict(sahna=sahna, nom=nom, t0=t0, cx=cx, cy=cy, h=h, **kw)


ELEMENTLAR = [
    # 1 — hook: uy, pul uchib ketadi, Quyoshvoy tepada
    E(1, "buyum_1", 0.10, 540, 1300, 520),
    E(1, "buyum_7", 0.90, 540, 1150, 200, yol=((540, 1150), (250, 640), 0.8), yoqol=1.9),
    E(1, "buyum_7", 1.90, 540, 1150, 200, yol=((540, 1150), (830, 600), 0.8), yoqol=2.9),
    E(1, "personaj_1", 2.50, 760, 640, 440, tebran=True),
    # 2 — Quyoshvoy salom, 3 ta sabab ikonkasi (raqamsiz)
    E(2, "personaj_1", 5.95, 540, 860, 680, tebran=True),
    E(2, "buyum_2", 7.30, 290, 1400, 230),
    E(2, "buyum_3", 7.65, 540, 1420, 250),
    E(2, "buyum_8", 8.00, 790, 1410, 210),
    # 3 — 1-sabab: panel tomga tushadi, pul kamayadi
    E(3, "buyum_1", 9.50, 540, 1180, 620),
    E(3, "personaj_2", 9.75, 240, 1400, 360, tebran=True),
    E(3, "buyum_2", 10.70, 560, 830, 210, yol=((560, 300), (560, 830), 0.30), kirish="tush"),
    E(3, "buyum_7", 12.60, 820, 1450, 230, kichray=(13.60, 0.5)),
    # 4 — 2-sabab, tun: akkumulyator va jihozlar
    E(4, "buyum_3", 18.00, 540, 1050, 460),
    E(4, "buyum_4", 19.50, 250, 1300, 400),
    E(4, "buyum_5", 20.30, 820, 790, 250),
    E(4, "buyum_6", 21.00, 820, 1330, 220),
    # 5 — 3-sabab: sarmoya (panel -> tangalar -> kopilka)
    E(5, "buyum_2", 23.40, 300, 760, 300),
    E(5, "personaj_3", 23.70, 790, 700, 400, tebran=True),
    E(5, "buyum_8", 25.50, 560, 1320, 440),
    E(5, "buyum_7", 26.65, 300, 900, 120, yol=((300, 900), (560, 1180), 0.35), yoqol=27.0, kirish="tush"),
    E(5, "buyum_7", 27.15, 300, 900, 120, yol=((300, 900), (560, 1180), 0.35), yoqol=27.5, kirish="tush"),
    E(5, "buyum_7", 27.65, 300, 900, 120, yol=((300, 900), (560, 1180), 0.35), yoqol=28.0, kirish="tush"),
    # 6 — xulosa: Quyoshvoy xursand sakraydi
    E(6, "personaj_5", 30.30, 540, 960, 720, sakra=True),
    # 7 — CTA: Quyoshvoy pastga ko'rsatadi
    E(7, "personaj_2", 33.75, 540, 980, 700, tebran=True),
]


# ---------------- yordamchilar ----------------

def _ease_out(u):
    return 1 - (1 - u) ** 3


def pop_masshtab(u):
    """80→106→100% (u: 0..1 POP_S ichida)."""
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
def stiker(nom, h):
    papka = ST_PERSONAJ if nom.startswith("personaj") else ST_BUYUM
    s = Image.open(papka / f"{nom}.png").convert("RGBA")
    return s.resize((max(1, round(s.width * h / s.height)), h), Image.LANCZOS)


def _alfa(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    return im


def _sahna_oraligi(n):
    return SAHNALAR[n - 1][0], SAHNALAR[n - 1][1]


# ---------------- kadr ----------------

def element_holati(e, t):
    """(cx, cy, masshtab, alfa) yoki None (ko'rinmaydi)."""
    s0, s1 = _sahna_oraligi(e["sahna"])
    if t < e["t0"] or t >= s1:
        return None
    u = t - e["t0"]
    cx, cy, m, a = e["cx"], e["cy"], 1.0, 1.0
    if "yol" in e:
        (x0, y0), (x1, y1), d = e["yol"]
        k = _ease_out(min(1.0, u / d)) if e.get("kirish") != "tush" else min(1.0, u / d) ** 2
        cx, cy = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    if e.get("kirish") == "tush":
        a = min(1.0, u / KIRISH_FADE_S)
    else:
        m = pop_masshtab(u / POP_S)
        a = min(1.0, u / KIRISH_FADE_S)
    if "yoqol" in e:                       # pul uchib ketib yo'qoladi / tanga kopilkaga kiradi
        if t >= e["yoqol"]:
            return None
        a *= min(1.0, (e["yoqol"] - t) / 0.2)
    if "kichray" in e and t >= e["kichray"][0]:
        tk, oxir = e["kichray"]
        m *= 1 - (1 - oxir) * _ease_out(min(1.0, (t - tk) / 0.3))
    if e.get("tebran") and u > POP_S:      # personaj: yengil tebranish (±8 px, 1.6 s)
        cy += 8 * math.sin(2 * math.pi * (u - POP_S) / 1.6)
    if e.get("sakra") and u > POP_S:       # sakrash: 0.6 s davr, 40 px
        cy -= 40 * abs(math.sin(math.pi * (u - POP_S) / 0.6))
    if t > s1 - CHIQISH_S:                 # sahna oxirida fade chiqish
        a *= max(0.0, (s1 - t) / CHIQISH_S)
    return cx, cy, m, a


def kadr(t):
    n = next(i for i, (a, b, _) in enumerate(SAHNALAR, 1) if a <= t < b or i == len(SAHNALAR))
    s0, _, f = SAHNALAR[n - 1]
    im = fon(f).copy()
    if n > 1 and SAHNALAR[n - 2][2] != f and t - s0 < 0.3:   # kun<->tun o'tishi 0.3 s
        im = Image.blend(fon(SAHNALAR[n - 2][2]), im, (t - s0) / 0.3)
    for e in ELEMENTLAR:
        if e["sahna"] != n:
            continue
        h = element_holati(e, t)
        if h is None:
            continue
        cx, cy, m, a = h
        s = stiker(e["nom"], max(2, round(e["h"] * m)))
        s = _alfa(s, a)
        im.alpha_composite(s, (round(cx - s.width / 2), round(cy - s.height / 2)))
    if t > DAVOMIYLIK - CHIQISH_S:         # oxirgi kadrda butun ekran fade
        im = Image.blend(Image.new("RGBA", im.size, (0, 0, 0, 255)), im,
                         max(0.0, (DAVOMIYLIK - t) / CHIQISH_S))
    return im.convert("RGB")


def safe_zona_tekshir():
    """Har element to'liq kattalikda safe zona ichidami (x 80–1000 yon elementlar, y 230–1595)."""
    xato = []
    for e in ELEMENTLAR:
        s = stiker(e["nom"], e["h"])
        pts = [(e["cx"], e["cy"])]
        if "yol" in e:
            pts += [e["yol"][0], e["yol"][1]]
        for cx, cy in pts:
            if e.get("kirish") == "tush" and (cx, cy) == e["yol"][0]:
                continue                    # tushish boshlanishi (fade bilan, kichik)
            x0, x1 = cx - s.width / 2, cx + s.width / 2
            y0, y1 = cy - s.height / 2 - (40 if e.get("sakra") else 8), cy + s.height / 2 + 8
            if x0 < 80 or x1 > 1000 or y0 < 230 or y1 > 1595:
                xato.append((e["nom"], e["t0"], round(x0), round(y0), round(x1), round(y1)))
    return xato


if __name__ == "__main__":
    buyruq = sys.argv[1]
    if buyruq == "kadr":
        out = Path("kesh/anim_kadr"); out.mkdir(parents=True, exist_ok=True)
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
                              "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                              "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", chiq],
                             stdin=subprocess.PIPE)
        for i in range(n):
            p.stdin.write(kadr(i / FPS).tobytes())
        p.stdin.close()
        sys.exit(p.wait())
