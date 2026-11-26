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
DAVOMIYLIK = 34.95
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
    E(1, "buyum_1", 0.15, 540, 600, 320, urg=[3.54]),
    E(1, "buyum_3", 0.75, 265, 520, 130),
    E(1, "buyum_4", 2.15, 815, 560, 170),
    # 2 — salom, logo ("SmartUzbek"), 3 sabab ikonkalari ("uchta sabab")
    E(2, "logo", 6.24, 540, 560, 300),
    E(2, "buyum_3", 8.22, 300, 790, 110),
    E(2, "buyum_5", 8.45, 540, 790, 130),
    E(2, "harf:ö:sariq", 8.68, 780, 790, 110),
    # 3 — 1-sabab: telefon, ovozli xabar telefonga kiradi ("yuborasiz"), hujjat chiqadi ("matnga aylanadi")
    E(3, "buyum_2", 9.15, 540, 610, 340),
    E(3, "buyum_3", 10.74, 540, 580, 150, yol=((250, 470), (540, 580), 0.35), yoqol=11.15, kirish="uch"),
    E(3, "buyum_4", 11.54, 805, 580, 220, yol=((540, 610), (805, 580), 0.35)),
    # 4 — 2-sabab: hujjat, qalam ustidan o'tadi ("tuzatib"), yashil belgi ("beradi")
    E(4, "buyum_4", 15.40, 500, 590, 320),
    E(4, "buyum_5", 17.30, 680, 640, 190, yol=((320, 500), (680, 640), 0.50), kirish="uch"),
    E(4, "buyum_6", 17.78, 790, 740, 140),
    # 5 — 3-sabab: eski yozuv ("eski") -> yangi harflar ("yangi yozuvga"), "Yangi harflar" — urg'u
    E(5, "harf:o‘:oq", 21.00, 270, 540, 110), E(5, "harf:g‘:oq", 21.12, 450, 540, 110),
    E(5, "harf:sh:oq", 21.24, 630, 540, 110), E(5, "harf:ch:oq", 21.36, 810, 540, 110),
    E(5, "harf:ö:sariq", 22.30, 270, 760, 130, urg=[23.80]), E(5, "harf:ğ:sariq", 22.45, 450, 760, 130, urg=[23.95]),
    E(5, "harf:ş:sariq", 22.60, 630, 760, 130, urg=[24.10]), E(5, "harf:ç:sariq", 22.75, 810, 760, 130, urg=[24.25]),
    # 6 — "hozircha bepul": sovg'a qutisi, "bepul" — urg'u
    E(6, "buyum_7", 25.00, 540, 600, 320, urg=[27.52]),
    # 7 — CTA: telefon ekranida logo
    E(7, "telefon_logo", 28.05, 540, 600, 390),
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


@lru_cache(maxsize=64)
def subtitr_rasm(matn):
    o = 66 * S
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    while True:
        f = shrift(o)
        l, tt, r, b = d.textbbox((0, 0), matn, font=f)
        if r - l + 72 * S <= 720 * S:
            break
        o -= 2 * S
    pw, ph = 36 * S, 22 * S
    im = Image.new("RGBA", (r - l + 2 * pw, b - tt + 2 * ph), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=26 * S, fill=(0, 6, 24, 165))
    dd.text((pw - l, ph - tt), matn, font=f, fill=(255, 255, 255, 255))
    return im


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
            s = _alfa(subtitr_rasm(c["matn"]), a)
            cy = 330 * S + (1 - k) * (12 if ulangan else 36) * S
            im.alpha_composite(s, (round(W / 2 - s.width / 2), round(cy - s.height / 2)))
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
