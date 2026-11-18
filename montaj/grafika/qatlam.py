"""To'liq kadrli qoraytirish qatlamlari (blur shape layer'da emas, butun kadrda — chetidan kesilmaydi)."""
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from ..qoidalar import KADR_BOYI as H, KADR_ENI as W, QOIDALAR


def _alfa_qatlam(alfa: np.ndarray) -> Image.Image:
    q = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    q.putalpha(Image.fromarray(np.clip(alfa * 255, 0, 255).astype(np.uint8)))
    return q


@lru_cache(maxsize=4)
def pastki_gradient(kuch=QOIDALAR.th.qoraytirish_kuch, balandlik=QOIDALAR.th.qoraytirish_balandlik):
    """Pastdan tepaga: pastda `kuch`, kadr balandligining `balandlik` qismida 0."""
    y = np.arange(H, dtype=float)
    tepa = H * (1 - balandlik)
    a = np.clip((y - tepa) / (H - tepa), 0, 1) * kuch
    return _alfa_qatlam(np.repeat(a[:, None], W, axis=1))


@lru_cache(maxsize=4)
def tepa_gradient(kuch: float, pastgacha_px: int):
    y = np.arange(H, dtype=float)
    a = np.clip(1 - y / pastgacha_px, 0, 1) * kuch
    return _alfa_qatlam(np.repeat(a[:, None], W, axis=1))


@lru_cache(maxsize=16)
def yumshoq_tasma(markaz_y: int, balandlik: int, kuch: float, blur_px: int = 70):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse([60, markaz_y - balandlik / 2, W - 60, markaz_y + balandlik / 2], fill=int(255 * kuch))
    m = m.filter(ImageFilter.GaussianBlur(blur_px))
    q = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    q.putalpha(m)
    return q


def opacity(q: Image.Image, k: float) -> Image.Image:
    if k >= 0.999:
        return q
    a = q.getchannel("A").point(lambda v: int(v * k))
    q = q.copy()
    q.putalpha(a)
    return q
