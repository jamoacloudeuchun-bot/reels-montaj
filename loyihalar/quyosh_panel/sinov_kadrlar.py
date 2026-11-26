"""Sinov kadrlari (render emas): stikerlar + fon + matn kompozitsiyasi, 1080x1920."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASL = Image.open("asl/chatgpt_v1_umumiy.png").convert("RGB")
ST = Path("kesh/stiker")
SHRIFT = "/home/user/reels-montaj/shriftlar/Oswald/Oswald-VariableFont_wght.ttf"
W, H = 1080, 1920
OQ = (255, 255, 255)


def fon(qaysi):
    box = (209, 608, 606, 1229) if qaysi == "kun" else (649, 609, 1046, 1229)
    f = ASL.crop(box)
    k = H / f.height
    f = f.resize((round(f.width * k), H), Image.LANCZOS)
    x = (f.width - W) // 2
    return f.crop((x, 0, x + W, H))


def stiker(kadr, nom, cx, cy, balandlik):
    s = Image.open(ST / f"{nom}.png")
    k = balandlik / s.height
    s = s.resize((round(s.width * k), balandlik), Image.LANCZOS)
    kadr.paste(s, (cx - s.width // 2, cy - s.height // 2), s)


def shrift(o, wght=700):
    f = ImageFont.truetype(SHRIFT, o)
    try:
        f.set_variation_by_axes([wght])
    except Exception:
        pass
    return f


def matn_karta(kadr, matn, cy, o=84, cx=W // 2, maks=760):
    """Oq matn, orqasida yarim shaffof to'q karta (soya yo'q)."""
    d0 = ImageDraw.Draw(kadr)
    f = shrift(o)
    l, t, r, b = d0.textbbox((0, 0), matn, font=f)
    while r - l > maks - 80:
        o -= 4; f = shrift(o); l, t, r, b = d0.textbbox((0, 0), matn, font=f)
    w, h = r - l + 80, b - t + 56
    qatlam = Image.new("RGBA", kadr.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(qatlam)
    d.rounded_rectangle((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2), radius=28, fill=(15, 20, 45, 190))
    d.text((cx - (r - l) // 2 - l, cy - (b - t) // 2 - t), matn, font=f, fill=OQ)
    kadr.alpha_composite(qatlam)


def kadr_1():
    k = fon("kun").convert("RGBA")
    stiker(k, "buyum_1", 540, 1330, 520)
    stiker(k, "buyum_7", 820, 1080, 210)
    stiker(k, "buyum_7", 300, 760, 190)
    stiker(k, "personaj_1", 770, 760, 420)
    matn_karta(k, "HAR OY TO'LAYSIZ?", 420)
    return k


def kadr_3():
    k = fon("kun").convert("RGBA")
    stiker(k, "buyum_1", 540, 1150, 560)
    stiker(k, "buyum_2", 700, 830, 260)
    stiker(k, "personaj_2", 250, 1380, 360)
    matn_karta(k, "1 · Svet puli kamayadi", 420, o=76)
    return k


def kadr_4():
    k = fon("tun").convert("RGBA")
    stiker(k, "buyum_3", 540, 980, 420)
    stiker(k, "buyum_4", 270, 1180, 380)
    stiker(k, "buyum_5", 800, 800, 230)
    stiker(k, "buyum_6", 810, 1240, 210)
    matn_karta(k, "2 · Svet o'chsa ham yorug'", 420, o=72)
    return k


def kadr_7():
    k = fon("kun").convert("RGBA")
    stiker(k, "personaj_2", 540, 1000, 620)
    matn_karta(k, "Izohda yozing: 1, 2 yoki 3?", 420, o=72)
    return k


if __name__ == "__main__":
    out = Path("kesh/sinov"); out.mkdir(parents=True, exist_ok=True)
    for nom, fn in (("01_hook", kadr_1), ("03_sabab1", kadr_3), ("04_sabab2", kadr_4), ("07_cta", kadr_7)):
        fn().convert("RGB").save(out / f"{nom}.png")
        print(nom)
