"""Shrift yuklash, matnni qatorlarga bo'lish va chizish (faqat oq, soyasiz)."""
import itertools
from functools import lru_cache

from PIL import ImageDraw, ImageFont

from ..loyiha import shrift_yoli
from ..qoidalar import QOIDALAR

OQ = (255, 255, 255, 255)


@lru_cache(maxsize=64)
def shrift(fayl: str, olcham: int, vazn: str | None = None):
    f = ImageFont.truetype(str(shrift_yoli(fayl)), olcham)
    if vazn:
        f.set_variation_by_name(vazn)
    return f


def uzunlik(matn: str, f, tracking: int = 0) -> float:
    return f.getlength(matn) + tracking * max(0, len(matn) - 1)


def qatorlarga(matn: str, f, eni_max: int, tracking: int = 0, qator_max: int = 3):
    """Eng kam qator, so'ng eng teng qatorlar (eng uzun qator eng qisqa) — so'zlar tartibi o'zgarmaydi."""
    w = matn.split()
    for n in range(1, min(qator_max, len(w)) + 1):
        eng = None
        for kes in itertools.combinations(range(1, len(w)), n - 1):
            idx = (0,) + kes + (len(w),)
            q = [" ".join(w[a:b]) for a, b in zip(idx, idx[1:])]
            m = max(uzunlik(x, f, tracking) for x in q)
            if m <= eni_max and (eng is None or m < eng[0]):
                eng = (m, q)
        if eng:
            return eng[1]
    return None                     # sig'madi — chaqiruvchi shriftni kichraytiradi


def sigdir(matn, fayl, vazn, eni_max, olcham_max, olcham_min=28, tracking=0, qator_max=3, majburiy_qatorlar=None):
    """Matn eni_max ga sig'adigan eng katta shrift o'lchami va qatorlar."""
    for s in range(olcham_max, olcham_min - 1, -2):
        f = shrift(fayl, s, vazn)
        if majburiy_qatorlar:
            if max(uzunlik(q, f, tracking) for q in majburiy_qatorlar) <= eni_max:
                return f, list(majburiy_qatorlar)
            continue
        q = qatorlarga(matn, f, eni_max, tracking, qator_max)
        if q:
            return f, q
    raise ValueError(f"matn {eni_max}px ga {olcham_min}px da ham sig'madi: {matn!r}")


def blok_chiz(qatlam, qatorlar, f, markaz_x, markaz_y, qator_oraligi, tracking=0, dy=0):
    """Qatorlarni markazga tekislab chizadi. Qaytaradi: har qator bbox (x0, y0, x1, y1)."""
    assert QOIDALAR.matn.tracking[0] <= tracking <= QOIDALAR.matn.tracking[1], "tracking CLAUDE.md doirasidan tashqarida"
    d = ImageDraw.Draw(qatlam)
    lh = qator_oraligi
    y0 = markaz_y - lh * len(qatorlar) / 2 + dy
    qutilar = []
    for i, q in enumerate(qatorlar):
        x = markaz_x - uzunlik(q, f, tracking) / 2
        y = y0 + i * lh + lh / 2
        if tracking == 0:
            d.text((x, y), q, font=f, fill=OQ, anchor="lm")
        else:
            for ch in q:
                d.text((x, y), ch, font=f, fill=OQ, anchor="lm")
                x += f.getlength(ch) + tracking
        bx = d.textbbox((markaz_x - uzunlik(q, f, tracking) / 2, y), q, font=f, anchor="lm")
        qutilar.append(bx)
    return qutilar
