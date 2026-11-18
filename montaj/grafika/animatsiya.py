"""CLAUDE.md animatsiya egri chiziqlari (vaqt — element boshlanganidan beri soniya)."""
from ..qoidalar import QOIDALAR

A = QOIDALAR.anim
POP_S = 0.30                    # 0.2–0.34 s oralig'ida
POP_CHOQQI_S = 0.18
CHIQISH_S = 0.25                # 0.2–0.3 s oralig'ida
KIRISH_OPACITY_S = 0.10


def ease_out(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def _lerp(a, b, x):
    return a + (b - a) * x


def pop_shkala(t: float) -> float:
    """80 % -> 106 % -> 100 %."""
    p0, p1, p2 = (v / 100 for v in A.pop_foiz)
    if t < POP_CHOQQI_S:
        return _lerp(p0, p1, ease_out(t / POP_CHOQQI_S))
    return _lerp(p1, p2, ease_out((t - POP_CHOQQI_S) / (POP_S - POP_CHOQQI_S)))


def kirish_kotarilish(t: float):
    """Matn pastdan ~36 px ko'tariladi, 0.2 s fade. Qaytaradi: (dy_px, opacity)."""
    x = ease_out(t / A.matn_fade_s)
    return round(A.matn_kotarilish_px * (1 - x)), x


def chiqish(t_qolgan: float, davom: float = CHIQISH_S) -> float:
    """Oxirgi `davom` soniyada 1 -> 0."""
    return min(1.0, max(0.0, t_qolgan / davom))


def zoom_zarba(t: float, choqqi_foiz: float = 110) -> float:
    """Ta'kid so'zda: 100 -> ~110 % (0.3 s kirish), qaytish 0.35 s. Tovushsiz."""
    if t < 0:
        return 1.0
    if t < A.zoom_kirish_s:
        return _lerp(1.0, choqqi_foiz / 100, ease_out(t / A.zoom_kirish_s))
    return _lerp(choqqi_foiz / 100, 1.0, ease_out((t - A.zoom_kirish_s) / A.zoom_chiqish_s))
