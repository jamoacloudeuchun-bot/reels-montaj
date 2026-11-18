"""Universal grafik elementlar. Har biri natija vaqtida [boshi, oxiri) ko'rinadi.

`chiz(t, kadr)` — t: natija videodagi soniya; kadr: RGBA qatlam (ustiga chiziladi).
Qaytaradi: chizilgan matn va kartochkalar qutilari [(x0, y0, x1, y1)] — safe zona tekshiruvi uchun.
Matn har doim oq; kartochka foni grafik element (to'q, yarim shaffof).
"""
from dataclasses import dataclass, field

from PIL import Image, ImageDraw

from ..qoidalar import KADR_ENI as W, QOIDALAR
from . import animatsiya as an
from .qatlam import opacity, pastki_gradient, tepa_gradient, yumshoq_tasma
from .shrift import blok_chiz, shrift, sigdir

Q = QOIDALAR


@dataclass
class Element:
    boshi: float
    oxiri: float
    chap_min = Q.safe.x[0]                       # safe zona chap chegarasi (kartochkalarda 80)

    def korinadi(self, t):
        return self.boshi <= t < self.oxiri

    def chiz(self, t, kadr):
        raise NotImplementedError


@dataclass
class PastkiGradient(Element):
    def chiz(self, t, kadr):
        if self.korinadi(t):
            kadr.alpha_composite(pastki_gradient())
        return []


@dataclass
class Hook(Element):
    """Sarlavha (y ≈ 420): pop 80→106→100 %, chiqishda fade. Soya yo'q — tepada yumshoq qoraytirish."""
    matn: str
    uslub: dict
    qatorlar: list | None = None
    _qatlam: Image.Image | None = field(default=None, init=False, repr=False)
    _qutilar: list = field(default_factory=list, init=False, repr=False)

    def _tayyorla(self):
        sh = self.uslub["shrift"]["sarlavha"]
        eni = self.uslub.get("eni_px", {}).get("sarlavha", Q.safe.markaz_matn_eni_max - 20)
        f, qatorlar = sigdir(self.matn, sh["fayl"], sh["vazn"], eni, self.uslub["olcham_px"]["sarlavha_max"],
                             qator_max=3, majburiy_qatorlar=self.qatorlar)
        q = Image.new("RGBA", kadr_olchami(), (0, 0, 0, 0))
        lh = int(f.size * self.uslub["qator_oraligi"]["sarlavha"])
        self._qutilar = blok_chiz(q, qatorlar, f, W // 2, Q.th.hook_y, lh)
        self._qatlam, self.qatorlar, self.olcham = q, qatorlar, f.size

    def chiz(self, t, kadr):
        if not self.korinadi(t):
            return []
        if self._qatlam is None:
            self._tayyorla()
        tt = t - self.boshi
        op = min(1.0, tt / an.KIRISH_OPACITY_S) * an.chiqish(self.oxiri - t)
        qr = self.uslub["qoraytirish"]["sarlavha_ortida"]
        if qr:
            kadr.alpha_composite(opacity(tepa_gradient(qr["kuch"], qr["pastgacha_px"]), op))
        s = an.pop_shkala(tt)
        x0 = min(b[0] for b in self._qutilar); y0 = min(b[1] for b in self._qutilar)
        x1 = max(b[2] for b in self._qutilar); y1 = max(b[3] for b in self._qutilar)
        blok = self._qatlam.crop((x0, y0, x1, y1))
        if abs(s - 1) > 1e-3:
            blok = blok.resize((max(1, round(blok.width * s)), max(1, round(blok.height * s))), Image.LANCZOS)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        px, py = round(cx - blok.width / 2), round(cy - blok.height / 2)
        kadr.alpha_composite(opacity(blok, op), (px, py))
        return [(px, py, px + blok.width, py + blok.height)]


@dataclass
class Subtitr(Element):
    """Subtitr (y ≈ 1260): pastdan 36 px ko'tarilib 0.2 s fade; ortida yumshoq qoraytirish."""
    matn: str
    uslub: dict
    chiqish_s: float = 0.2

    def chiz(self, t, kadr):
        if not self.korinadi(t):
            return []
        sh = self.uslub["shrift"]["subtitr"]
        eni = self.uslub.get("eni_px", {}).get("subtitr", 760)
        olcham = self.uslub["olcham_px"]["subtitr"]
        f, qatorlar = sigdir(self.matn, sh["fayl"], sh["vazn"], eni, olcham, olcham_min=40,
                             qator_max=self.uslub.get("subtitr_qator_max", 3))
        lh = int(olcham * self.uslub["qator_oraligi"]["subtitr"])
        dy, op = an.kirish_kotarilish(t - self.boshi)
        op *= an.chiqish(self.oxiri - t, self.chiqish_s)
        qr = self.uslub["qoraytirish"]["subtitr_ortida"]
        if qr:
            kadr.alpha_composite(opacity(yumshoq_tasma(Q.th.subtitr_y, len(qatorlar) * lh + 170, qr["kuch"],
                                                       qr.get("blur_px", 70)), op))
        q = Image.new("RGBA", kadr.size, (0, 0, 0, 0))
        qutilar = blok_chiz(q, qatorlar, f, W // 2, Q.th.subtitr_y, lh, dy=dy)
        kadr.alpha_composite(opacity(q, op))
        return qutilar


@dataclass
class Kartochka(Element):
    """Yon/pastki kartochka: to'q yarim shaffof fon, ustida kichik izoh (~44 px) va asosiy so'z. Pop bilan kiradi."""
    sarlavha: str
    izoh: str | None
    uslub: dict
    y_markaz: int = 1260
    # pop 106 % da ham [80, 930] ichida qolishi uchun: eni 800, markaz 505
    x0: int = 105
    x1: int = 905
    chap_min = Q.safe.yon_kartochka_min_x      # yon kartochka chapdan ~x 80 dan boshlanishi mumkin

    def chiz(self, t, kadr):
        if not self.korinadi(t):
            return []
        tt = t - self.boshi
        op = min(1.0, tt / an.KIRISH_OPACITY_S) * an.chiqish(self.oxiri - t)
        sh, iz = self.uslub["shrift"]["sarlavha"], self.uslub["shrift"]["izoh"]
        fs = shrift(sh["fayl"], 76, sh["vazn"])
        fi = shrift(iz["fayl"], Q.matn.izoh_px, iz["vazn"])
        bal = 76 + (Q.matn.izoh_px + 16 if self.izoh else 0) + 70
        q = Image.new("RGBA", kadr.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(q)
        y0 = self.y_markaz - bal / 2
        d.rounded_rectangle([self.x0, y0, self.x1, y0 + bal], radius=28, fill=(10, 14, 28, 205))
        x = self.x0 + 44
        y = y0 + 35
        if self.izoh:
            d.text((x, y), self.izoh, font=fi, fill=(255, 255, 255, 255), anchor="lt")
            y += Q.matn.izoh_px + 16
        d.text((x, y), self.sarlavha, font=fs, fill=(255, 255, 255, 255), anchor="lt")
        quti = (self.x0, int(y0), self.x1, int(y0 + bal))
        s = an.pop_shkala(tt)
        blok = q.crop(quti)
        if abs(s - 1) > 1e-3:
            blok = blok.resize((round(blok.width * s), round(blok.height * s)), Image.LANCZOS)
        px = round((quti[0] + quti[2]) / 2 - blok.width / 2)
        py = round((quti[1] + quti[3]) / 2 - blok.height / 2)
        kadr.alpha_composite(opacity(blok, op), (px, py))
        return [(px, py, px + blok.width, py + blok.height)]


@dataclass
class Royxat(Element):
    """Ro'yxat/sanash uchun to'liq ekran grafika (CLAUDE.md: split ekran o'rniga).

    Bandlar `bandlar_vaqti` (boshlanishdan soniya) bo'yicha birin-ketin pastdan ko'tarilib chiqadi.
    """
    sarlavha: str
    bandlar: list
    uslub: dict
    bandlar_vaqti: list | None = None
    fon_kuchi: float = 0.88

    def chiz(self, t, kadr):
        if not self.korinadi(t):
            return []
        tt = t - self.boshi
        op = min(1.0, tt / 0.15) * an.chiqish(self.oxiri - t)
        fon = Image.new("RGBA", kadr.size, (8, 10, 18, int(255 * self.fon_kuchi)))
        kadr.alpha_composite(opacity(fon, op))
        sh = self.uslub["shrift"]["sarlavha"]
        f, qatorlar = sigdir(self.sarlavha, sh["fayl"], sh["vazn"], Q.safe.markaz_matn_eni_max - 20, 96, qator_max=2)
        q = Image.new("RGBA", kadr.size, (0, 0, 0, 0))
        qutilar = blok_chiz(q, qatorlar, f, W // 2, Q.th.hook_y, int(f.size * 1.08))
        fb = shrift(self.uslub["shrift"]["subtitr"]["fayl"], 58, self.uslub["shrift"]["subtitr"]["vazn"])
        vaqt = self.bandlar_vaqti or [0.3 + 0.35 * i for i in range(len(self.bandlar))]
        y = max(b[3] for b in qutilar) + 110
        for i, (band, bt) in enumerate(zip(self.bandlar, vaqt)):
            if tt < bt:
                break
            dy, bop = an.kirish_kotarilish(tt - bt)
            b = Image.new("RGBA", kadr.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(b)
            matn = f"{i + 1}. {band}"
            d.text((Q.safe.x[0] + 40, y + dy), matn, font=fb, fill=(255, 255, 255, 255), anchor="lt")
            qutilar.append(d.textbbox((Q.safe.x[0] + 40, y + dy), matn, font=fb, anchor="lt"))
            q.alpha_composite(opacity(b, bop))
            y += 110
        kadr.alpha_composite(opacity(q, op))
        return qutilar


def kadr_olchami():
    from ..qoidalar import KADR_BOYI, KADR_ENI
    return (KADR_ENI, KADR_BOYI)
