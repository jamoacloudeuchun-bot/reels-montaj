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
        """Barcha ko'rinadigan elementlar. "Bir so'z bir vaqtda bitta joyda": subtitrni yashiruvchi
        grafika (masalan to'liq ekran sahna yoki kartochka) ko'rinib turganda subtitr chizilmaydi."""
        q = Image.new("RGBA", (KADR_ENI, KADR_BOYI), (0, 0, 0, 0))
        yashir = any(getattr(e, "subtitrni_yashiradi", False) and e.korinadi(t) for e in self.elementlar)
        qutilar = []
        for e in self.elementlar:
            if yashir and isinstance(e, Subtitr):
                continue
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
    el += grafikalar_qur(getattr(lo, "grafikalar", None), uslub, matn_n["sozlar"], nat, dav)
    return Sahna(el, dav, fps, orl)


def _komponentlar(uslub) -> dict:
    """Yadro elementlari + uslub paketi komponentlari (uslublar/<nom>/<fayl>.py dagi KOMPONENTLAR)."""
    from .grafika.elementlar import Kartochka, Royxat
    k = {"Kartochka": Kartochka, "Royxat": Royxat}
    fayl = uslub.get("komponentlar")
    if fayl:
        import importlib.util
        from pathlib import Path
        yol = Path(uslub["_papka"]) / fayl
        spec = importlib.util.spec_from_file_location(f"uslub_{uslub['nomi']}_komponentlar", yol)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        k.update(mod.KOMPONENTLAR)
    return k


def grafikalar_qur(tavsif, uslub, sozlar, nat, dav):
    """loyiha.json "grafikalar": [{"tur": ..., "boshi_s"/"soz": ..., "oxiri_s"/"davom_s": ..., ...}].

    Vaqtlar MANBA videosi bo'yicha (soniya) yoki so'z bo'yicha ("soz", "takror"). Qolgan maydonlar
    komponentga parametr bo'lib o'tadi. Matnlar faqat loyiha faylidan — avtomatik ko'chirilmaydi.
    """
    if not tavsif:
        return []
    from .matn import normal
    komp = _komponentlar(uslub)
    natija = []
    for g in tavsif:
        g = dict(g)
        tur = g.pop("tur")
        if tur not in komp:
            raise ValueError(f"noma'lum grafika turi: {tur}. Mavjud: {', '.join(sorted(komp))}")
        if "soz" in g:
            soz, n = g.pop("soz"), g.pop("takror", 1)
            mos = [s for s in sozlar if normal(s["soz"]) == normal(soz)]
            if len(mos) < n:
                raise ValueError(f"grafika uchun so'z topilmadi: {soz!r}")
            boshi = nat(mos[n - 1]["boshi"])
        else:
            boshi = nat(g.pop("boshi_s"))
        oxiri = nat(g.pop("oxiri_s")) if "oxiri_s" in g else min(dav, boshi + g.pop("davom_s", 2.5))
        g.pop("_izoh", None)                                   # loyiha fayli uchun izoh (komponentga o'tmaydi)
        natija.append(komp[tur](boshi, oxiri, uslub=uslub, **g))
    return natija


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
