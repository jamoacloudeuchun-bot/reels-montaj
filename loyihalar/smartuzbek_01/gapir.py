"""Gapiruvchi personaj: har pozada og'iz (vizem) almashadi va ko'z qirpiydi.

Joylar yuz.json dan (yuz_top.py avtomatik topadi). Og'iz va yopiq ko'z dasturda vektor uslubida
chiziladi — har qanday o'lchamda (4K ham) tiniq. Vizem tanlash: lab_sinov.vizem_chizigi
(ovoz energiyasi + Whisper so'z vaqtlaridagi unli harf).

API:  yuz = YuzKadr("stikerlar/poza", "yuz.json")
      im = yuz.kadr("poza_1", vizem="A", koz_yumuq=False, k=1.6)   # k — kattalashtirish
"""
import json
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from lab_sinov import KONTUR, ogiz  # noqa: E402

ASL_OGIZ_ENI = 52   # lab_sinov.ogiz() k=1 dagi taxminiy og'iz eni (px)


class YuzKadr:
    def __init__(self, papka, yuz_json):
        self.papka = Path(papka)
        self.joy = json.load(open(yuz_json))

    @lru_cache(maxsize=64)
    def _asos(self, poza, k):
        """Kattalashtirilgan poza, og'zi o'chirilgan (teri rangi bilan)."""
        im = Image.open(self.papka / f"{poza}.png").convert("RGBA")
        if k != 1:
            im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        j = self.joy[poza]
        x0, y0, x1, y1 = [v * k for v in j["ogiz"]]
        teri = im.getpixel((round((x0 + x1) / 2), round(y1 + 6 * k)))
        d = ImageDraw.Draw(im)
        px, py = 5 * k, 4 * k
        d.ellipse((x0 - px, y0 - py, x1 + px, y1 + py), fill=teri)
        return im

    @lru_cache(maxsize=64)
    def _yumuq(self, poza, k):
        """Ko'zlar yopiq holat: ko'z oqi va qorachiq teri rangi bilan yopiladi, ustiga yoy chiziladi."""
        im = self._asos(poza, k).copy()
        d = ImageDraw.Draw(im)
        for x0, y0, x1, y1 in self.joy[poza]["kozlar"]:
            x0, y0, x1, y1 = x0 * k, y0 * k, x1 * k, y1 * k
            teri = _atrof_teri(im, x0, y0, x1, y1, k)
            e = 4.5 * k   # ko'z chetidagi qora chiziq (kiprik) ham yopilsin
            d.ellipse((x0 - e, y0 - e, x1 + e, y1 + e), fill=teri)
            _oq_qoldiq(im, x0 - e - 4 * k, y0 - e - 4 * k, x1 + e + 4 * k, y1 + e + 4 * k, teri)
            cy = y0 + (y1 - y0) * 0.55
            d.arc((x0, cy - (y1 - y0) * 0.35, x1, cy + (y1 - y0) * 0.35), 15, 165, fill=KONTUR,
                  width=max(2, round(2.6 * k)))
        return im

    def kadr(self, poza, vizem="X", koz_yumuq=False, k=1.0):
        im = (self._yumuq(poza, k) if koz_yumuq else self._asos(poza, k)).copy()
        j = self.joy[poza]
        x0, y0, x1, y1 = [v * k for v in j["ogiz"]]
        m = _ogiz_rasm(vizem, round((x1 - x0) / ASL_OGIZ_ENI * 100))   # x0..x1 allaqachon k marta
        # og'iz markazi: asl og'iz chizig'ining markazidan biroz yuqori (ochilganda pastga cho'ziladi)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 - 1 * k
        im.alpha_composite(m, (round(cx - m.width / 2), round(cy - m.height / 2)))
        return im


def _oq_qoldiq(im, x0, y0, x1, y1, teri):
    """Ellips chetida qolgan ko'z oqi bo'laklarini (oq piksellar) teri rangiga bo'yash."""
    import numpy as np
    box = (round(x0), round(y0), round(x1), round(y1))
    a = np.asarray(im.crop(box)).copy()
    oq = (a[..., :3].min(2) > 205) & (a[..., 3] > 0)
    a[oq] = teri
    im.paste(Image.fromarray(a, "RGBA"), box[:2])


def _atrof_teri(im, x0, y0, x1, y1, k):
    """Ko'z atrofidagi (linza ichidagi) terining median rangi: qora/oq piksellar hisobga olinmaydi."""
    import numpy as np
    e = 9 * k
    a = np.asarray(im.crop((round(x0 - e), round(y0 - e), round(x1 + e), round(y1 + e))).convert("RGB")).astype(int)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy, rx, ry = w / 2, h / 2, (x1 - x0) / 2 + 5 * k, (y1 - y0) / 2 + 5 * k
    halqa = (((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2) > 1
    teri = (a.sum(2) > 330) & (a.min(2) < 215) & (a[..., 0] > a[..., 2] + 40)
    m = a[halqa & teri]
    return tuple(int(v) for v in np.median(m, axis=0)) + (255,) if len(m) > 10 else (253, 197, 146, 255)


@lru_cache(maxsize=256)
def _ogiz_rasm(vizem, k100):
    return ogiz(vizem, k=k100 / 100)


def qirpish_vaqtlari(davomiylik, seed=7):
    """Har 2.8–5 s da 0.12 s ko'z qirpish (tasodifiy, lekin takrorlanuvchan)."""
    import random
    r = random.Random(seed)
    t, res = 1.2, []
    while t < davomiylik:
        res.append((t, t + 0.12))
        t += r.uniform(2.8, 5.0)
    return res
