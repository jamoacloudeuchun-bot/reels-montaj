"""SmartUzbek 01: "Botni sinab ko'rish uchun 3 sabab" — stiker animatsiyasi.

Quyosh paneli loyihasidagi qoidalar asosida (personaj pastda, buyumlar tepada, subtitr tepada,
Instagram safe zona x 150–930, y 230–1595; pop 80→106→100%; chiqish 0.25 s fade; matn oq, soyasiz).
Yangi: jurnalist og'zi gapga mos qimirlaydi (gapir.py + lab_sinov.vizem_chizigi), ko'z qirpiydi;
fon dasturda chiziladi (fon.py); logo oq kartada; ö ğ ş ç harf kartalari.
Vaqtlar: Whisper so'z vaqtlari (sozlar_whisper.json). Koordinatalar 1080x1920 tizimida, S marta.

  python animatsiya.py kadr 3.6 11.0 17.6 23.9           # sinov kadrlari (render emas)
  python animatsiya.py tekshir                           # butun video bo'ylab piksel safe zona tekshiruvi
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

sys.path.insert(0, str(Path(__file__).parent))
from fon import fon as fon_chiz  # noqa: E402
from gapir import YuzKadr, qirpish_vaqtlari  # noqa: E402
from lab_sinov import vizem_chizigi  # noqa: E402

S = 2
W, H, FPS = 1080 * S, 1920 * S, 60
OVOZ = "kesh/ovoz/ovoz_final.wav"
DAVOMIYLIK = 37.00   # ovoz 36.29 s (asl tezlik) + 0.7 s
SHRIFT_SUB = "/home/user/reels-montaj/shriftlar/Oswald/Oswald-VariableFont_wght.ttf"
SHRIFT_HARF = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
KOK, SARIQ, OQ = (2, 43, 122, 255), (253, 192, 5, 255), (255, 255, 255, 255)
SAFE = (150, 230, 930, 1595)

POP_S, KIRISH_FADE_S, CHIQISH_S = 0.30, 0.10, 0.25

SAHNALAR = [(0.00, 4.90), (4.90, 9.10), (9.10, 15.30), (15.30, 20.30),
            (20.30, 24.90), (24.90, 27.95), (27.95, DAVOMIYLIK)]

# jurnalist: oyoqlari y=1585, balandligi ~720 px; poza almashganda pop
PERSONAJ_OYOQ, PERSONAJ_H = (540, 1585), 720
POZALAR = [(0.05, "poza_6"), (4.94, "poza_1"), (9.12, "poza_6"), (15.32, "poza_4"), (18.24, "poza_3"),
           (20.36, "poza_6"), (27.45, "poza_5"), (28.00, "poza_2")]


def E(sahna, nom, t0, cx, cy, h, **kw):
    return dict(sahna=sahna, nom=nom, t0=t0, cx=cx, cy=cy, h=h, **kw)


ELEMENTLAR = [
    # 1 — hook: qum soat ("soatlik"), ovozli xabar ("ovozli"), hujjat ("matnga"); "soatlab" — urg'u
    E(1, "buyum_1", 0.15, 540, 510, 384, urg=[3.54]),
    E(1, "buyum_3", 0.75, 265, 430, 156),
    E(1, "buyum_4", 2.15, 815, 470, 204),
    # 2 — salom, logo ("SmartUzbek"), 3 sabab ikonkalari ("uchta sabab")
    E(2, "logo", 6.24, 540, 470, 360),
    E(2, "buyum_3", 8.22, 300, 700, 132),
    E(2, "buyum_5", 8.45, 540, 700, 156),
    E(2, "harf:ö:sariq", 8.68, 780, 700, 132),
    # 3 — 1-sabab: telefon, ovozli xabar telefonga kiradi ("yuborasiz"), hujjat chiqadi ("matnga aylanadi")
    E(3, "buyum_2", 9.15, 540, 520, 408),
    E(3, "buyum_3", 10.74, 540, 490, 180, yol=((250, 380), (540, 490), 0.35), yoqol=11.15, kirish="uch"),
    E(3, "buyum_4", 11.54, 805, 490, 264, yol=((540, 520), (805, 490), 0.35)),
    # 4 — 2-sabab: hujjat, qalam ustidan o'tadi ("tuzatib"), yashil belgi ("beradi")
    E(4, "buyum_4", 15.40, 500, 500, 384),
    E(4, "buyum_5", 17.30, 680, 550, 228, yol=((320, 410), (680, 550), 0.50), kirish="uch"),
    E(4, "buyum_6", 17.78, 790, 650, 168),
    # 5 — 3-sabab: eski yozuv ("eski") -> yangi harflar ("yangi yozuvga"), "Yangi harflar" — urg'u
    E(5, "harf:o‘:oq", 21.00, 270, 450, 132), E(5, "harf:g‘:oq", 21.12, 450, 450, 132),
    E(5, "harf:sh:oq", 21.24, 630, 450, 132), E(5, "harf:ch:oq", 21.36, 810, 450, 132),
    E(5, "harf:ö:sariq", 22.30, 270, 670, 156, urg=[23.80]), E(5, "harf:ğ:sariq", 22.45, 450, 670, 156, urg=[23.95]),
    E(5, "harf:ş:sariq", 22.60, 630, 670, 156, urg=[24.10]), E(5, "harf:ç:sariq", 22.75, 810, 670, 156, urg=[24.25]),
    # 6 — "hozircha bepul": sovg'a qutisi, "bepul" — urg'u
    E(6, "buyum_7", 25.00, 540, 510, 384, urg=[27.52]),
    # 7 — CTA: telefon ekranida logo
    E(7, "telefon_logo", 28.05, 540, 510, 468),
]


# Vaqtlar 1.06 tezlikdagi ovoz bo'yicha yozilgan; asl tezlikdagi ovoz uchun chiziqli kattalashtiriladi.
VAQT_K = 1.06
SAHNALAR = [(round(a * VAQT_K, 3), round(b * VAQT_K, 3) if b < 34.9 else DAVOMIYLIK) for a, b in SAHNALAR]
POZALAR = [(round(t * VAQT_K, 3), p) for t, p in POZALAR]
for _e in ELEMENTLAR:
    _e["t0"] = round(_e["t0"] * VAQT_K, 3)
    if "yoqol" in _e:
        _e["yoqol"] = round(_e["yoqol"] * VAQT_K, 3)
    if "urg" in _e:
        _e["urg"] = [round(u * VAQT_K, 3) for u in _e["urg"]]


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


def urg_masshtab(t, vaqtlar):
    """Urg'u zarbasi (CLAUDE.md): 100→110%, 0.3 s kirish, 0.35 s chiqish; tovushsiz."""
    m = 1.0
    for tu in vaqtlar or []:
        u = t - tu
        if 0 <= u < 0.3:
            m = max(m, 1 + 0.10 * _ease_out(u / 0.3))
        elif 0.3 <= u < 0.65:
            m = max(m, 1.10 - 0.10 * _ease_out((u - 0.3) / 0.35))
    return m


def _alfa(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    return im


@lru_cache(maxsize=1)
def fon():
    return fon_chiz(W, H)


@lru_cache(maxsize=None)
def _logo_karta(h):
    """Logo oq yumaloq kartada (logoning oq fonini kesmasdan, brendga mos)."""
    lg = Image.open("asl/logo.jpg").convert("RGBA")
    bb = Image.eval(lg.convert("L"), lambda v: 255 if v < 235 else 0).getbbox()
    lg = lg.crop((bb[0] - 30, bb[1] - 30, bb[2] + 30, bb[3] + 30))
    k = h / lg.height
    lg = lg.resize((round(lg.width * k), h), Image.LANCZOS)
    karta = Image.new("RGBA", lg.size, (0, 0, 0, 0))
    m = Image.new("L", lg.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, lg.width - 1, lg.height - 1), radius=round(h * 0.12), fill=255)
    karta.paste(lg, (0, 0), m)
    return karta


@lru_cache(maxsize=None)
def _harf(matn, rang, h):
    im = Image.new("RGBA", (h, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fill = SARIQ if rang == "sariq" else OQ
    d.rounded_rectangle((0, 0, h - 1, h - 1), radius=round(h * 0.22), fill=fill,
                        outline=(1, 20, 60, 255), width=max(2, round(h * 0.045)))
    o = round(h * (0.62 if len(matn) == 1 else 0.46))
    f = ImageFont.truetype(SHRIFT_HARF, o)
    l, t, r, b = d.textbbox((0, 0), matn, font=f)
    d.text(((h - (r - l)) / 2 - l, (h - (b - t)) / 2 - t), matn, font=f, fill=KOK)
    return im


@lru_cache(maxsize=None)
def _buyum(nom):
    return Image.open(f"stikerlar/buyum/{nom}.png").convert("RGBA")


@lru_cache(maxsize=512)
def stiker(nom, h):
    if nom == "logo":
        return _logo_karta(h)
    if nom.startswith("harf:"):
        _, m, rang = nom.split(":")
        return _harf(m, rang, h)
    if nom == "telefon_logo":
        tel = stiker("buyum_2", h).copy()
        lg = _logo_karta(round(h * 0.42))
        lg = lg.resize((round(tel.width * 0.66), round(tel.width * 0.66 * lg.height / lg.width)), Image.LANCZOS)
        tel.alpha_composite(lg, ((tel.width - lg.width) // 2, (tel.height - lg.height) // 2))
        return tel
    s = _buyum(nom)
    return s.resize((max(1, round(s.width * h / s.height)), h), Image.LANCZOS)


def sahna_raqami(t):
    for i, (a, b) in enumerate(SAHNALAR, 1):
        if a <= t < b:
            return i
    return len(SAHNALAR)


def element_holati(e, t):
    s0, s1 = SAHNALAR[e["sahna"] - 1]
    if t < e["t0"] or t >= s1:
        return None
    u = t - e["t0"]
    cx, cy, m = e["cx"], e["cy"], 1.0
    if "yol" in e:
        (x0, y0), (x1, y1), d = e["yol"]
        k = _ease_out(min(1.0, u / d))
        cx, cy = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    a = min(1.0, u / KIRISH_FADE_S)
    if e.get("kirish") != "uch":
        m = pop_masshtab(u / POP_S)
    if "yoqol" in e:
        if t >= e["yoqol"]:
            return None
        a *= min(1.0, (e["yoqol"] - t) / 0.15)
        m *= 1 - 0.5 * max(0.0, 1 - (e["yoqol"] - t) / 0.2)   # telefonga kirayotib kichrayadi
    m *= urg_masshtab(t, e.get("urg"))
    if u > POP_S and "yol" not in e:
        cy += 4 * math.sin(2 * math.pi * (u - POP_S) / 2.2 + e["t0"])
    if t > s1 - CHIQISH_S:
        a *= max(0.0, (s1 - t) / CHIQISH_S)
    return cx, cy, m, a


# ---------------- personaj ----------------

YUZ = YuzKadr("stikerlar/poza", "yuz.json")
K_PERSONAJ = PERSONAJ_H * S / 610


@lru_cache(maxsize=1)
def vizemlar():
    return vizem_chizigi(OVOZ, "sozlar_whisper.json", FPS)


@lru_cache(maxsize=1)
def qirpish():
    return qirpish_vaqtlari(DAVOMIYLIK)


@lru_cache(maxsize=1)
def energiya_qator():
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", OVOZ, "-ac", "1", "-ar", "48000", "-f", "f32le", "-"],
                       capture_output=True, check=True)
    x = np.frombuffer(r.stdout, np.float32)
    h = 480
    n = len(x) // h
    db = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)
    e = np.clip((db + 42) / 24, 0, 1)
    out = np.zeros_like(e)
    for i in range(1, n):
        k = 0.28 if e[i] > out[i - 1] else 0.08
        out[i] = out[i - 1] + k * (e[i] - out[i - 1])
    return out


def energiya(t):
    e = energiya_qator()
    i = int(t * 100)
    return float(e[i]) if 0 <= i < len(e) else 0.0


def personaj(im, t):
    if t < POZALAR[0][0]:
        return
    joriy = max((p for p in POZALAR if p[0] <= t), key=lambda p: p[0])
    u = t - joriy[0]
    i = int(t * FPS)
    viz = vizemlar()[i] if i < len(vizemlar()) else "X"
    yumuq = any(a <= t < b for a, b in qirpish())
    st = YUZ.kadr(joriy[1], viz, yumuq, k=K_PERSONAJ)
    e = energiya(t)
    m = pop_masshtab(u / POP_S)
    a = min(1.0, (t - POZALAR[0][0]) / KIRISH_FADE_S)
    sy, sx = m * (1 + 0.03 * e), m * (1 - 0.015 * e)
    burchak = 2.0 * math.sin(2 * math.pi * t / 1.3) * (0.35 + 0.65 * e)
    kotar = 10 * e
    if joriy[1] == "poza_5":
        kotar += 40 * abs(math.sin(math.pi * u / 0.55))
    if abs(sx - 1) > 1e-3 or abs(sy - 1) > 1e-3:
        st = st.resize((round(st.width * sx), round(st.height * sy)), Image.BICUBIC)
    st = _alfa(st, a)
    r = st.rotate(burchak, resample=Image.BICUBIC, expand=True)
    rad = math.radians(burchak)
    dy = st.height / 2
    rx, ry = dy * math.sin(rad), dy * math.cos(rad)
    fx, fy = PERSONAJ_OYOQ[0] * S, (PERSONAJ_OYOQ[1] - kotar) * S
    im.alpha_composite(r, (round(fx - rx - r.width / 2), round(fy - ry - r.height / 2)))


# ---------------- subtitr ----------------

@lru_cache(maxsize=1)
def subtitrlar():
    return json.load(open("subtitr.json"))


@lru_cache(maxsize=8)
def shrift(o):
    f = ImageFont.truetype(SHRIFT_SUB, o)
    try:
        f.set_variation_by_axes([600])
    except Exception:
        pass
    return f


# Subtitr pastda, personajning oyoqlari ustida (yuz va qo'llar ochiq qoladi). Matn har doim oq (CLAUDE.md);
# sariq faqat urg'u chizig'i / lenta chetida.
import os  # noqa: E402
SUB_USLUB = os.environ.get("SUB_USLUB", "B")   # tanlangan: B karaoke (A karta | C katta | D lenta)
SUB_Y = 1420
SHRIFT_KATTA = "/usr/share/fonts/opentype/inter/Inter-Black.otf"


def _sigdir(matn, shr, o, maks):
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    while True:
        f = shr(o)
        l, tt, r, b = d.textbbox((0, 0), matn, font=f)
        if r - l <= maks:
            return f, (l, tt, r, b)
        o -= 2 * S


@lru_cache(maxsize=8)
def shrift_katta(o):
    return ImageFont.truetype(SHRIFT_KATTA, o)


@lru_cache(maxsize=256)
def subtitr_rasm(matn, uslub="A", faol=-1):
    """faol — karaoke uslubida hozir aytilayotgan so'z indeksi."""
    if uslub == "C":
        matn = matn.upper()
        f, (l, tt, r, b) = _sigdir(matn, shrift_katta, 84 * S, 700 * S)
        sw = 7 * S
        im = Image.new("RGBA", (r - l + 2 * sw + 8, b - tt + 2 * sw + 8), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((sw + 4 - l, sw + 4 - tt), matn, font=f, fill=(255, 255, 255, 255),
                                stroke_width=sw, stroke_fill=(1, 18, 58, 255))
        return im
    f, (l, tt, r, b) = _sigdir(matn, shrift, 64 * S, (720 - 90) * S)
    pw, ph = 36 * S, 22 * S
    chap = 14 * S if uslub == "D" else 0
    im = Image.new("RGBA", (r - l + 2 * pw + chap, b - tt + 2 * ph + (8 * S if uslub == "B" else 0)), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    if uslub == "D":
        dd.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=18 * S, fill=(2, 43, 122, 235))
        dd.rounded_rectangle((0, 0, chap + 8 * S, im.height - 1), radius=18 * S, fill=SARIQ)
        dd.rectangle((chap, 0, chap + 8 * S, im.height - 1), fill=(2, 43, 122, 235))
    else:
        dd.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=26 * S, fill=(0, 6, 24, 170))
    x0 = pw + chap - l
    dd.text((x0, ph - tt), matn, font=f, fill=(255, 255, 255, 255))
    if uslub == "B" and faol >= 0:
        sozlar = matn.split(" ")
        oldi = " ".join(sozlar[:faol]) + (" " if faol else "")
        xa = x0 + l + dd.textlength(oldi, font=f)
        xb = xa + dd.textlength(sozlar[faol], font=f)
        y = ph - tt + b + 4 * S
        dd.rounded_rectangle((xa, y, xb, y + 6 * S), radius=3 * S, fill=SARIQ)
    return im


KARAOKE_KECHIKISH = 0.12   # Whisper so'z boshlari ~0.2 s oldinda (CLAUDE.md), chiziq so'z bilan birga yursin


def _faol_soz(c, t):
    """Bo'lak ichida qaysi so'z aytilyapti: Whisper so'z boshlari bo'yicha (bo'lmasa — uzunlikka mutanosib)."""
    if "sozlar" in c:
        i = 0
        for k, ts in enumerate(c["sozlar"]):
            if t >= ts + (KARAOKE_KECHIKISH if k else 0):
                i = k
        return i
    sozlar = c["matn"].split(" ")
    uz = [len(w) + 1 for w in sozlar]
    u = (t - c["a"]) / max(0.05, c["b"] - c["a"]) * sum(uz)
    jam = 0
    for i, n in enumerate(uz):
        jam += n
        if u < jam:
            return i
    return len(sozlar) - 1


def subtitr(im, t):
    sl = subtitrlar()
    for i, c in enumerate(sl):
        if c["a"] <= t < c["b"]:
            u = t - c["a"]
            ulangan = i and abs(sl[i - 1]["b"] - c["a"]) < 0.01
            d = 0.08 if ulangan else 0.2
            k = _ease_out(min(1.0, u / d))
            a = k
            keyingi = sl[i + 1] if i + 1 < len(sl) else None
            if not (keyingi and abs(keyingi["a"] - c["b"]) < 0.01):
                a *= min(1.0, (c["b"] - t) / 0.2)
            faol = _faol_soz(c, t) if SUB_USLUB == "B" else -1
            s = subtitr_rasm(c["matn"], SUB_USLUB, faol)
            dx, dy = 0, (1 - k) * (12 if ulangan else 36) * S
            if SUB_USLUB == "C":                      # har bo'lak pop bilan
                m = pop_masshtab(u / 0.24)
                s = s.resize((max(1, round(s.width * m)), max(1, round(s.height * m))), Image.BICUBIC)
                dy = 0
            elif SUB_USLUB == "D" and not ulangan:    # chapdan sirpanib kiradi
                dx, dy = -(1 - k) * 40 * S, 0
            s = _alfa(s, a)
            cy = SUB_Y * S + dy
            im.alpha_composite(s, (round(W / 2 - s.width / 2 + dx), round(cy - s.height / 2)))
            return


# ---------------- kadr ----------------

def kadr(t):
    n = sahna_raqami(t)
    im = fon().copy()
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


def piksel_tekshir(qadam=0.1):
    """Butun video bo'ylab: fon bilan farq qilgan piksellar safe zona ichidami."""
    x0, y0, x1, y1 = [v * S for v in SAFE]
    b = np.asarray(fon().convert("RGB")).astype(np.int16)
    yomon, umumiy = [], [10 ** 9, 10 ** 9, 0, 0]
    for i in range(int(DAVOMIYLIK / qadam)):
        t = i * qadam
        if t > DAVOMIYLIK - CHIQISH_S:
            continue
        k = np.asarray(kadr(t)).astype(np.int16)
        ys, xs = np.nonzero(np.abs(k - b).max(2) > 12)
        if len(xs) == 0:
            continue
        bb = (xs.min(), ys.min(), xs.max(), ys.max())
        umumiy = [min(umumiy[0], bb[0]), min(umumiy[1], bb[1]), max(umumiy[2], bb[2]), max(umumiy[3], bb[3])]
        if bb[0] < x0 or bb[1] < y0 or bb[2] > x1 or bb[3] > y1:
            yomon.append((round(t, 2), [int(v / S) for v in bb]))
    return [int(v / S) for v in umumiy], yomon


if __name__ == "__main__":
    buyruq = sys.argv[1]
    if buyruq == "kadr":
        out = Path("kesh/anim_kadr"); out.mkdir(parents=True, exist_ok=True)
        for v in map(float, sys.argv[2:]):
            kadr(v).save(out / f"t{v:05.2f}.png")
            print(out / f"t{v:05.2f}.png")
    elif buyruq == "tekshir":
        umumiy, yomon = piksel_tekshir()
        print("umumiy chegaralar:", umumiy, "| chiqib ketgan kadrlar:", len(yomon), yomon[:10])
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
