"""Sahna: natija vaqt o'qidagi grafik elementlar, kadr ustiga qatlam va safe zona tekshiruvi."""
from dataclasses import dataclass

from PIL import Image

from .grafika.elementlar import Hook, PastkiGradient, Subtitr
from .qoidalar import KADR_BOYI, KADR_ENI, QOIDALAR
from .subtitr import jadval
from .vaqt import fps_qiymat, kadr_vaqti

S = QOIDALAR.safe


def manba_vaqti_natijaga(t, oraliqlar, fps):
    """Manba vaqti -> natija vaqti; kesilgan joyga tushsa, keyingi saqlangan bo'lak boshi."""
    f = float(fps_qiymat(fps))
    oldingi = 0
    for a, b in oraliqlar:
        if t < a / f:
            return oldingi / f
        if t < b / f:
            return (oldingi + t * f - a) / f
        oldingi += b - a
    return oldingi / f


@dataclass
class Sahna:
    elementlar: list
    davomiylik: float
    fps: object
    oraliqlar: list

    def qatlam(self, t):
        q = Image.new("RGBA", (KADR_ENI, KADR_BOYI), (0, 0, 0, 0))
        qutilar = []
        for e in self.elementlar:
            for b in e.chiz(t, q):
                qutilar.append((e, b))
        return q, qutilar

    def manba_kadri(self, t):
        """Natija vaqti -> manba kadr raqami."""
        n = int(round(t * float(fps_qiymat(self.fps))))
        for a, b in self.oraliqlar:
            if n < b - a:
                return a + n
            n -= b - a
        a, b = self.oraliqlar[-1]
        return b - 1


def sahna_qur(lo, uslub, matn_n, kesish_n) -> Sahna:
    fps = kesish_n["fps"]
    orl = [tuple(x) for x in kesish_n["saqlanadigan_kadrlar"]]
    dav = kesish_n["natija_kadr"] / float(fps_qiymat(fps))
    hook_or, bol = jadval(matn_n["sozlar"], uslub, lo.hook)
    nat = lambda t: round(manba_vaqti_natijaga(t, orl, fps), 4)     # noqa: E731
    el = []
    if uslub["qoraytirish"].get("pastki_gradient"):
        el.append(PastkiGradient(0, dav))
    if hook_or:
        el.append(Hook(0.0, nat(hook_or[1]), lo.hook, uslub, qatorlar=uslub.get("_hook_qatorlar")))
    for i, b in enumerate(bol):
        oxirgi = i == len(bol) - 1
        oxiri = dav if oxirgi else nat(b["oxiri"])
        # Chiqish fade faqat oxirgi subtitrda; ketma-ketlarida keskin almashuv (yangisi kirish animatsiyasi bilan)
        el.append(Subtitr(nat(b["boshi"]), oxiri, b["matn"], uslub, chiqish_s=0.2 if oxirgi else 0.0))
    return Sahna(el, dav, fps, orl)


def safe_tekshir(sahna: Sahna, qadam_s: float = 1 / 30):
    """Har qadamda barcha qutilarni tekshiradi. Qaytaradi: buzilishlar ro'yxati (bo'sh — hammasi joyida)."""
    xato = []
    t = 0.0
    while t < sahna.davomiylik:
        _, qutilar = sahna.qatlam(t)
        for e, (x0, y0, x1, y1) in qutilar:
            nom = type(e).__name__
            if x0 < e.chap_min - 0.5 or x1 > S.x[1] + 0.5 or y0 < S.y[0] - 0.5 or y1 > S.y[1] + 0.5:
                xato.append({"t": round(t, 3), "element": nom, "quti": [x0, y0, x1, y1], "sabab": "safe zonadan tashqarida"})
            if nom in ("Hook", "Subtitr") and x1 - x0 > S.markaz_matn_eni_max + 0.5:
                xato.append({"t": round(t, 3), "element": nom, "eni": x1 - x0, "sabab": "markaziy matn eni > 780"})
        t += qadam_s
    return xato


def natija_kadr_vaqti(kadr, fps):
    return kadr_vaqti(kadr, fps)
