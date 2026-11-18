"""Soniya va kadr raqami o'rtasidagi hisoblar.

CLAUDE.md: "Kesimlarni kadr raqami bilan qil (aks holda ovoz va video siljiydi)."
Barcha kesimlar kadr chegarasiga tushadi; ovoz ham shu kadr vaqtlarida kesiladi.
"""
import math
from fractions import Fraction


def fps_qiymat(fps) -> Fraction:
    """'60/1', '30000/1001', 60 yoki 59.94 -> aniq kasr."""
    if isinstance(fps, Fraction):
        return fps
    if isinstance(fps, str) and "/" in fps:
        a, b = fps.split("/")
        return Fraction(int(a), int(b))
    x = float(fps)
    for n in (24, 30, 48, 60, 120):          # NTSC: 23.976, 29.97, 59.94 …
        if abs(x - n * 1000 / 1001) < 0.005:
            return Fraction(n * 1000, 1001)
    return Fraction(x).limit_denominator(1001)


def kadr_vaqti(kadr: int, fps) -> float:
    return float(kadr / fps_qiymat(fps))


def kadrga(t: float, fps, usul: str = "yaqin") -> int:
    """Soniyani kadr raqamiga: 'past' (floor), 'yuqori' (ceil) yoki 'yaqin' (round)."""
    x = t * float(fps_qiymat(fps))
    eps = 1e-9
    if usul == "past":
        return int(math.floor(x + eps))
    if usul == "yuqori":
        return int(math.ceil(x - eps))
    return int(math.floor(x + 0.5))


def oraliqlar_uzunligi(oraliqlar) -> int:
    """[(boshi, oxiri_exclusive), ...] -> jami kadr."""
    return sum(b - a for a, b in oraliqlar)


def manbadan_natijaga(t: float, oraliqlar, fps):
    """Manba vaqti -> natija videodagi vaqt (kesilgan joyda bo'lsa None)."""
    f = float(fps_qiymat(fps))
    oldingi = 0
    for a, b in oraliqlar:
        if a / f <= t < b / f:
            return (oldingi + (t * f - a)) / f
        oldingi += b - a
    return None
