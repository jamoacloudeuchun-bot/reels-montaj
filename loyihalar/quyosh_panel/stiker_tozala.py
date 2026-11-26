"""Kesilgan stikerlar chetidagi oq/kulrang "soya"ni (halo) olib tashlaydi va chetini silliqlaydi.

- buyum rejimi: tashqaridan boshlab oq kontur va kulrang chiziqni to'liq olib tashlaydi
  (to'yinganligi past, yorug' piksellar bo'ylab flood-fill), qora konturda to'xtaydi.
- personaj rejimi: dizayndagi oq konturni saqlaydi, faqat tashqi kulrang chiziqni (1–2 px) oladi.
Ikkalasida: mayda qoldiq bo'laklar o'chiriladi, alfa cheti 1 px yumshatiladi (zinapoya yo'q).

Ishlatish: python stiker_tozala.py buyum|personaj kirish_papka chiqish_papka
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
from stiker_kes import _kengay, komponentlar  # noqa: E402


def _toldir_dan(boshlang, ruxsat):
    m = boshlang & ruxsat
    while True:
        n = _kengay(m, 1) & ruxsat
        if (n == m).all():
            return m
        m = n


def tozala(im, rejim):
    im = im.convert("RGBA")
    pad = 4
    a = np.asarray(im).astype(int)
    a = np.pad(a, ((pad, pad), (pad, pad), (0, 0)))
    rgb, al = a[..., :3], a[..., 3]
    mx, mn = rgb.max(2), rgb.min(2)
    shaffof = al < 10
    if rejim == "buyum":
        # oq kontur + kulrang soya; juda och (pushtimtir/yashilsimon) hoshiya ham
        och = ((mn >= 200) & (mx - mn <= 16)) | ((mn >= 222) & (mx - mn <= 40))
    else:
        och = (mn >= 150) & (mn <= 246) & (mx - mn <= 16)  # faqat kulrang chiziq, oq kontur qoladi
    fon = _toldir_dan(_kengay(shaffof, 1), shaffof | och)
    obyekt = ~fon
    # mayda qoldiqlarni o'chirish: eng katta komponentga nisbatan 2% dan kichiklar
    belgi, komp = komponentlar(obyekt, min_maydon=1)
    if komp:
        eng = max(k[5] for k in komp)
        for k in komp:
            if k[5] < 0.02 * eng:
                obyekt[belgi == k[4]] = False
    alfa = Image.fromarray((obyekt * 255).astype(np.uint8))
    alfa = alfa.filter(ImageFilter.MinFilter(5 if rejim == "buyum" else 3)).filter(ImageFilter.GaussianBlur(0.8))
    rgb_im = Image.fromarray(rgb.astype(np.uint8))
    out = rgb_im.convert("RGBA")
    out.putalpha(alfa)
    bb = out.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    return out.crop(bb)


if __name__ == "__main__":
    rejim, kir, chiq = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    chiq.mkdir(parents=True, exist_ok=True)
    for f in sorted(kir.glob("*.png")):
        r = tozala(Image.open(f), rejim)
        r.save(chiq / f.name)
        print(f.name, Image.open(f).size, "->", r.size)
