"""Andoza_01 uslub komponentlari (yadrodan alohida; yadro bu faylni faqat uslub tanlanganda yuklaydi).

REFERENCES/Andoza_01 dagi tuzilish qayta ishlatiladigan komponentlarga aylantirilgan va CLAUDE.md ga
moslashtirilgan:
- barcha matn OQ (QOIDALAR.matn.rang); oltin rang faqat grafik element, ikonka va ✓ belgisida;
- soya va blur yo'q; tracking 0–20; matn va kartochkalar safe zona ichida;
- kirish: pop 80→106→100 % yoki 36 px ko'tarilish + 0.2 s fade; chiqish 0.25 s fade;
- andozadagi matnlar, logotiplar va brend nomlari ko'chirilmaydi — barcha matn loyiha faylidan keladi.

Har komponent `qatlamlar(tt)` -> (grafika, matn, qutilar) qaytaradi: matn alohida qatlamda — testlar
undagi piksellar faqat oq ekanini tekshiradi.
"""
import math
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw

from montaj.grafika import animatsiya as an
from montaj.grafika.elementlar import Element
from montaj.grafika.qatlam import opacity
from montaj.grafika.shrift import blok_chiz, qatorlarga, shrift, sigdir, uzunlik
from montaj.qoidalar import KADR_BOYI as H, KADR_ENI as W, QOIDALAR

Q = QOIDALAR
OQ = (255, 255, 255, 255)
SS = 4                                   # ikonka va doiralar uchun supersampling


def rang(h: str, alfa: float = 1.0):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (int(round(255 * alfa)),)


def _bosh():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


@lru_cache(maxsize=4)
def navy_fon(tepa: str, past: str, bezak_alfa: float) -> Image.Image:
    """To'liq ekran fon: vertikal gradient + ingichka yoylar + pastda perspektiv to'r (grafika, matn emas)."""
    a, b = np.array(rang(tepa)[:3], float), np.array(rang(past)[:3], float)
    k = np.linspace(0, 1, H)[:, None]
    g = (a * (1 - k) + b * k).astype(np.uint8)
    img = Image.fromarray(np.repeat(g[:, None, :], W, axis=1).reshape(H, W, 3), "RGB").convert("RGBA")
    bez = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(bez)
    c = (255, 255, 255, int(255 * bezak_alfa))
    for cx, cy, r in [(2400, 300, 1500), (-300, 2600, 1700), (2300, 3300, 1300)]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, width=4)
    ufq, past_y = 2 * 1480, 2 * H
    for i in range(9):                                   # gorizontal chiziqlar (perspektiva)
        y = ufq + (past_y - ufq) * (i / 8) ** 1.8
        d.line([(0, y), (2 * W, y)], fill=c, width=3)
    for i in range(-6, 7):                               # yaqinlashuvchi vertikallar
        d.line([(W + i * 120, ufq), (W + i * 520, past_y)], fill=c, width=3)
    img.alpha_composite(bez.resize((W, H), Image.LANCZOS))
    return img


def _ikonka(nom: str, px: int, chiziq: str) -> Image.Image:
    """Oddiy vektor ikonka (supersampling bilan): odam, hujjat, check, kalendar."""
    s = px * SS
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c, w = rang(chiziq), max(2, s // 14)
    m = s * 0.22
    if nom == "odam":
        r = s * 0.15
        d.ellipse([s / 2 - r, s * 0.24, s / 2 + r, s * 0.24 + 2 * r], outline=c, width=w)
        d.arc([s * 0.24, s * 0.58, s * 0.76, s * 1.06], 180, 360, fill=c, width=w)
    elif nom == "hujjat":
        d.rounded_rectangle([m, m * 0.8, s - m, s - m * 0.8], radius=s // 16, outline=c, width=w)
        for i, k in enumerate((0.4, 0.55, 0.7)):
            d.line([(m * 1.6, s * k), (s - m * (1.6 if i < 2 else 2.4), s * k)], fill=c, width=w)
    elif nom == "kalendar":
        d.rounded_rectangle([m, m * 1.1, s - m, s - m * 0.8], radius=s // 16, outline=c, width=w)
        d.line([(m, s * 0.42), (s - m, s * 0.42)], fill=c, width=w)
        for x in (0.38, 0.62):
            d.line([(s * x, m * 0.6), (s * x, m * 1.5)], fill=c, width=w)
    else:                                                 # "check"
        d.line([(s * 0.25, s * 0.52), (s * 0.43, s * 0.70), (s * 0.76, s * 0.33)], fill=c, width=w * 2, joint="curve")
    return im.resize((px, px), Image.LANCZOS)


def _check_doira(r: int, oltin: str, chiziq: str) -> Image.Image:
    s = 2 * r * SS
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, s - 1, s - 1], fill=rang(oltin))
    w = max(3, s // 9)
    d.line([(s * 0.28, s * 0.52), (s * 0.44, s * 0.68), (s * 0.73, s * 0.36)], fill=rang(chiziq), width=w, joint="curve")
    return im.resize((2 * r, 2 * r), Image.LANCZOS)


def _yoy(markaz, r, qalinlik, ulush, oltin) -> Image.Image:
    """Oltin doira chizig'i, `ulush` (0–1) qismi chizilgan (soat yo'nalishida, tepadan)."""
    s = SS
    im = Image.new("RGBA", (W * s // 2, H * s // 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = markaz[0] * s / 2, markaz[1] * s / 2
    rr = r * s / 2
    if ulush > 0:
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], -90, -90 + 360 * min(1, ulush), fill=rang(oltin),
              width=int(qalinlik * s / 2))
    return im.resize((W, H), Image.LANCZOS)


@dataclass(kw_only=True)
class AndozaElement(Element):
    uslub: dict
    kirish: str | None = None              # "pop" | "kotarilish"; None — uslubdagi qiymat
    subtitrni_yashiradi = True             # bir so'z bir vaqtda bitta joyda
    toliq_ekran = False
    toliq_korinish_s = 1.4                 # preview uchun: animatsiya tugagan payt

    @property
    def a(self):
        return self.uslub["andoza"]

    def _sh(self, rol, olcham):
        s = self.uslub["shrift"][rol]
        return shrift(s["fayl"], olcham, s["vazn"])

    def _yorliq(self, m, matn, y):
        f = self._sh("yorliq", self.uslub["olcham_px"]["yorliq"])
        return blok_chiz(m, [matn.upper()], f, W // 2, y, int(f.size * 1.2), tracking=self.uslub["tracking"]["yorliq"])

    def _sarlavha(self, m, matn, y, eni=None, tepa=None):
        """Sarlavha bloki: markazi y da; `tepa` berilsa — blok yuqori cheti shu y dan boshlanadi."""
        sh = self.uslub["shrift"]["sarlavha"]
        f, q = sigdir(matn, sh["fayl"], sh["vazn"], eni or self.uslub["eni_px"]["sarlavha"],
                      self.uslub["olcham_px"]["sarlavha_max"], qator_max=2)
        lh = int(f.size * self.uslub["qator_oraligi"]["sarlavha"])
        if tepa is not None:
            y = max(y, tepa + lh * len(q) / 2)
        return blok_chiz(m, q, f, W // 2, y, lh)

    def _bosh_qism(self, m, yorliq, sarlavha):
        """Yorliq + sarlavha (sarlavha hech qachon yorliq ustiga chiqmaydi). Qaytaradi: (qutilar, kontent y)."""
        j = self.a["joylashuv"]
        qut = []
        if yorliq:
            qut += self._yorliq(m, yorliq, j["yorliq_y"])
        if sarlavha:
            tepa = (qut[-1][3] + 18) if qut else None
            qut += self._sarlavha(m, sarlavha, j["sarlavha_y"], tepa=tepa)
        past = max((b[3] for b in qut), default=j["kontent_boshi_y"] - 60)
        return qut, int(round(max(j["kontent_boshi_y"], past + 70)))

    def qatlamlar(self, tt):
        raise NotImplementedError

    def chiz(self, t, kadr):
        if not self.korinadi(t):
            return []
        tt = t - self.boshi
        v = self.a["vaqt"]
        if self.toliq_ekran:
            r = self.a["ranglar"]
            kadr.alpha_composite(navy_fon(r["fon_tepa"], r["fon_past"], r["bezak_chiziq_alfa"]))
        kech = v["kontent_kechikish_s"] if self.toliq_ekran else 0.0
        kt = tt - kech
        if kt < 0:
            return []
        g, m, qut = self.qatlamlar(kt)
        if not qut:
            return []
        kontent = Image.alpha_composite(g, m)
        chizilgan = kontent.getbbox() or (0, 0, 0, 0)          # haqiqatan chizilgan hamma narsa
        x0, y0 = min([b[0] for b in qut] + [chizilgan[0]]), min([b[1] for b in qut] + [chizilgan[1]])
        x1, y1 = max([b[2] for b in qut] + [chizilgan[2]]), max([b[3] for b in qut] + [chizilgan[3]])
        op = min(1.0, kt / an.KIRISH_OPACITY_S) * an.chiqish(self.oxiri - t)
        usul = self.kirish or v["kirish"]
        if usul == "pop":
            s = an.pop_shkala(kt)
            blok = kontent.crop((x0, y0, x1, y1))
            if abs(s - 1) > 1e-3:
                blok = blok.resize((max(1, round(blok.width * s)), max(1, round(blok.height * s))), Image.LANCZOS)
            px, py = round((x0 + x1) / 2 - blok.width / 2), round((y0 + y1) / 2 - blok.height / 2)
            kadr.alpha_composite(opacity(blok, op), (px, py))
            return [(px, py, px + blok.width, py + blok.height)]
        dy, o2 = an.kirish_kotarilish(kt)
        q = _bosh()
        q.alpha_composite(kontent, (0, dy))
        kadr.alpha_composite(opacity(q, op * o2))
        return [(x0, y0 + dy, x1, y1 + dy)]


@dataclass(kw_only=True)
class LowerThird(AndozaElement):
    """Kamera ustidagi kartochka: oltin ikonka plitkasi + kichik yorliq + katta so'z (y ≈ 1265)."""
    matn: str
    yorliq: str | None = None
    ikonka: str | None = "check"
    chap_min = Q.safe.yon_kartochka_min_x
    toliq_korinish_s = 0.8

    def qatlamlar(self, tt):
        j, r = self.a["joylashuv"], self.a["ranglar"]
        g, m = _bosh(), _bosh()
        x0, x1 = j["lower_third_x"]
        h = j["lower_third_balandlik"]
        y0 = j["lower_third_y"] - h // 2
        ImageDraw.Draw(g).rounded_rectangle([x0, y0, x1, y0 + h], radius=j["radius"],
                                            fill=rang(r["lower_third"], r["lower_third_alfa"]))
        tx = x0 + 40
        if self.ikonka:
            ip = j["ikonka_px"]
            iy = y0 + (h - ip) // 2
            ImageDraw.Draw(g).rounded_rectangle([tx, iy, tx + ip, iy + ip], radius=j["radius"], fill=rang(r["oltin"]))
            g.alpha_composite(_ikonka(self.ikonka, int(ip * 0.8), r["ikonka_chiziq"]), (tx + ip // 10, iy + ip // 10))
            tx += ip + 36
        eni = x1 - 40 - tx
        d = ImageDraw.Draw(m)
        fy = self._sh("yorliq", self.uslub["olcham_px"]["yorliq"])
        sh = self.uslub["shrift"]["sarlavha"]
        f, q = sigdir(self.matn.upper(), sh["fayl"], sh["vazn"], eni, self.uslub["olcham_px"]["lower_third"],
                      olcham_min=40, qator_max=1)
        cap = lambda ft: ft.getbbox("H")[3] - ft.getbbox("H")[1]          # noqa: E731  bosh harf balandligi
        oraliq = 22
        jami = cap(f) + ((cap(fy) + oraliq) if self.yorliq else 0)
        tayanch = y0 + (h - jami) / 2
        if self.yorliq:
            tayanch += cap(fy)
            x, trk = tx, self.uslub["tracking"]["yorliq"]
            if uzunlik(self.yorliq.upper(), fy, trk) > eni:          # sig'masa: avval tracking 0, so'ng kichikroq
                trk = 0
                while uzunlik(self.yorliq.upper(), fy) > eni and fy.size > 36:
                    fy = self._sh("yorliq", fy.size - 2)
            for ch in self.yorliq.upper():                 # tracking (CLAUDE.md: 0–20), umumiy tayanch chiziq
                d.text((x, tayanch), ch, font=fy, fill=OQ, anchor="ls")
                x += fy.getlength(ch) + trk
            tayanch += oraliq
        d.text((tx, tayanch + cap(f)), q[0], font=f, fill=OQ, anchor="ls")
        return g, m, [(x0, y0, x1, y0 + h)]


@dataclass(kw_only=True)
class RaqamSahna(AndozaElement):
    """To'liq ekran: yorliq, sarlavha, katta raqam, birlik/izoh va ixtiyoriy shkala (oltin to'ldirish)."""
    raqam: str
    yorliq: str | None = None
    sarlavha: str | None = None
    birlik: str | None = None
    izoh: str | None = None
    shkala: list | None = None             # [min, max] — butun sonlar
    qiymat: list | None = None             # [a, b] yoki [a] — oltin bilan belgilanadigan oraliq
    toliq_ekran = True

    def qatlamlar(self, tt):
        g, m = _bosh(), _bosh()
        qut, y = self._bosh_qism(m, self.yorliq, self.sarlavha)
        sh = self.uslub["shrift"]["raqam"]
        f, q = sigdir(self.raqam, sh["fayl"], sh["vazn"], 700, self.uslub["olcham_px"]["raqam_max"], qator_max=1)
        qut += blok_chiz(m, q, f, W // 2, y + f.size // 2 + 20, f.size)
        y = qut[-1][3] + 40
        if self.birlik:
            fb = self._sh("band", 72)
            qut += blok_chiz(m, [self.birlik.upper()], fb, W // 2, y + 40, 80)
            y = qut[-1][3] + 30
        if self.izoh:
            fi = self._sh("yorliq", Q.matn.izoh_px)
            qut += blok_chiz(m, [self.izoh], fi, W // 2, y + 30, 60)
            y = qut[-1][3] + 30
        if self.shkala:
            qut += self._shkala(g, m, y + 80, tt)
        return g, m, qut

    def _shkala(self, g, m, y, tt):
        r = self.a["ranglar"]
        lo, hi = self.shkala
        x0, x1 = Q.safe.x[0] + 60, Q.safe.x[1] - 60          # pop 106 % da yorliqlar bilan ham safe zonada
        px = lambda v: x0 + (x1 - x0) * (v - lo) / max(1, hi - lo)      # noqa: E731
        d = ImageDraw.Draw(g)
        d.line([(x0, y), (x1, y)], fill=(255, 255, 255, 90), width=4)
        fi = shrift(self.uslub["shrift"]["izoh"]["fayl"], 40, None)
        dm = ImageDraw.Draw(m)
        for v in range(lo, hi + 1):
            d.line([(px(v), y - 14), (px(v), y + 14)], fill=(255, 255, 255, 140), width=3)
            dm.text((px(v), y + 34), str(v), font=fi, fill=OQ, anchor="mt")
        if self.qiymat:
            a, b = (self.qiymat + self.qiymat)[:2]
            k = an.ease_out(tt / self.a["vaqt"]["shkala_s"])
            xe = px(a) + (px(b) - px(a)) * k
            d.line([(px(a), y), (xe, y)], fill=rang(r["oltin"]), width=10)
            for xx in ([px(a), xe] if b != a else [px(a)]):
                d.ellipse([xx - 13, y - 13, xx + 13, y + 13], fill=rang(r["oltin"]))
        return [(x0 - 14, y - 16, x1 + 14, y + 34 + fi.size + 6)]


@dataclass(kw_only=True)
class ChecklistSahna(AndozaElement):
    """To'liq ekran ro'yxat: raqamli kartochkalar birin-ketin chiqadi, oltin ✓ belgilar qo'shiladi."""
    bandlar: list
    yorliq: str | None = None
    sarlavha: str | None = None
    belgilangan: list | None = None        # ✓ qo'yiladigan band indekslari (0 dan); None — hammasi
    toliq_ekran = True

    @property
    def toliq_korinish_s(self):
        v = self.a["vaqt"]
        return v["kontent_kechikish_s"] + v["band_oraligi_s"] * len(self.bandlar) + v["check_kechikish_s"] + 0.4

    def qatlamlar(self, tt):
        j, r, v = self.a["joylashuv"], self.a["ranglar"], self.a["vaqt"]
        g, m = _bosh(), _bosh()
        qut, y = self._bosh_qism(m, self.yorliq, self.sarlavha)
        bh, bo = j["band_balandlik"], j["band_oraligi"]
        if y + len(self.bandlar) * (bh + bo) > Q.safe.y[1]:
            raise ValueError(f"ro'yxat safe zonaga sig'maydi: {len(self.bandlar)} ta band")
        x0, x1 = j["karta_x"]
        fb = self._sh("band", self.uslub["olcham_px"]["band"])
        fn = self._sh("raqam", 40)
        belgi = set(range(len(self.bandlar)) if self.belgilangan is None else self.belgilangan)
        for i, band in enumerate(self.bandlar):
            bt = tt - i * v["band_oraligi_s"]
            if bt < 0:
                break
            dy, op = an.kirish_kotarilish(bt)
            yy = int(y + i * (bh + bo) + dy)
            bg, bm = _bosh(), _bosh()
            dg, dm = ImageDraw.Draw(bg), ImageDraw.Draw(bm)
            dg.rounded_rectangle([x0, yy, x1, yy + bh], radius=j["radius"], fill=rang(r["karta"], r["karta_alfa"]))
            cx, cy = x0 + 62, yy + bh // 2
            dg.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], outline=(255, 255, 255, 170), width=3)
            dm.text((cx, cy), str(i + 1), font=fn, fill=OQ, anchor="mm")
            eni = x1 - 110 - (x0 + 120) - 20
            matn = band
            while uzunlik(matn, fb) > eni and len(matn) > 1:
                fb = self._sh("band", fb.size - 2)
            dm.text((x0 + 120, cy), matn, font=fb, fill=OQ, anchor="lm")
            ct = bt - v["check_kechikish_s"]
            if i in belgi and ct >= 0:
                s = an.pop_shkala(ct)
                rr = max(1, round(30 * s))
                ch = _check_doira(30, r["oltin"], r["lower_third"]).resize((2 * rr, 2 * rr), Image.LANCZOS)
                bg.alpha_composite(ch, (x1 - 62 - rr, cy - rr))
            g.alpha_composite(opacity(bg, op))
            m.alpha_composite(opacity(bm, op))
            qut.append((x0, yy, x1, yy + bh))
        return g, m, qut


@dataclass(kw_only=True)
class SanaSahna(AndozaElement):
    """To'liq ekran: 1–3 ta sana kartochkasi (oy — kartochka sarlavhasida, kun — katta raqam, izoh)."""
    sanalar: list                          # [{"oy": "...", "kun": "...", "izoh": "..."}]
    yorliq: str | None = None
    sarlavha: str | None = None
    toliq_ekran = True

    def qatlamlar(self, tt):
        j, r = self.a["joylashuv"], self.a["ranglar"]
        g, m = _bosh(), _bosh()
        qut, y = self._bosh_qism(m, self.yorliq, self.sarlavha)
        n = len(self.sanalar)
        if not 1 <= n <= 3:
            raise ValueError("sanalar soni 1–3 bo'lishi kerak")
        x0, x1 = j["karta_x"]
        oraliq = 50
        kw = min(330, (x1 - x0 - 6 - oraliq * (n - 1)) // n)     # 6 px zaxira: pop 106 % da ham safe zonada
        jami = n * kw + (n - 1) * oraliq
        sx = (W - jami) // 2
        kh, sh_h = 330, 84
        dg, dm = ImageDraw.Draw(g), ImageDraw.Draw(m)
        fo = self._sh("yorliq", Q.matn.izoh_px)
        fk = self._sh("raqam", 170)
        fi = shrift(self.uslub["shrift"]["izoh"]["fayl"], 40, None)
        for i, s in enumerate(self.sanalar):
            kx = sx + i * (kw + oraliq)
            dg.rounded_rectangle([kx, y, kx + kw, y + kh], radius=j["radius"], fill=rang(r["karta"], r["karta_alfa"]))
            dg.rounded_rectangle([kx, y, kx + kw, y + sh_h], radius=j["radius"], fill=rang(r["lower_third"], 1.0),
                                 corners=(True, True, False, False))
            dg.line([(kx, y + sh_h), (kx + kw, y + sh_h)], fill=rang(r["oltin"]), width=6)     # oltin chiziq — grafika
            dm.text((kx + kw / 2, y + sh_h / 2), s["oy"].upper(), font=fo, fill=OQ, anchor="mm")
            dm.text((kx + kw / 2, y + sh_h + (kh - sh_h) / 2), str(s["kun"]), font=fk, fill=OQ, anchor="mm")
            if s.get("izoh"):
                dm.text((kx + kw / 2, y + kh + 26), s["izoh"], font=fi, fill=OQ, anchor="mt")
            qut.append((kx, y, kx + kw, y + kh + (26 + fi.size + 8 if s.get("izoh") else 0)))
        return g, m, qut


@dataclass(kw_only=True)
class DoiraSahna(AndozaElement):
    """To'liq ekran: oltin doira chiziladi, markazda katta raqam; ustida yorliq/sarlavha."""
    raqam: str
    yorliq: str | None = None
    sarlavha: str | None = None
    izoh: str | None = None
    joy: str = "toliq"                     # "toliq" — to'liq ekran; "yon" — yuz yonida ixcham kartochka
    markaz_x: int = 790                    # "yon" uchun kartochka markazi (x)
    markaz_y: int = 760                    # "yon" uchun kartochka markazi (y, ko'z darajasi atrofi)
    toliq_ekran = True

    def __post_init__(self):
        if self.joy == "yon":
            self.toliq_ekran = False
            self.toliq_korinish_s = 0.9

    def _yon(self, tt):
        """Yuz yonidagi ixcham kartochka: yorliq, oltin doira ichida belgi, izoh (2 qatorgacha)."""
        r, j = self.a["ranglar"], self.a["joylashuv"]
        g, m = _bosh(), _bosh()
        eni = 270
        x0 = int(self.markaz_x - eni / 2)
        x0 = max(Q.safe.x[0] + 12, min(x0, Q.safe.x[1] - 12 - eni))      # pop 106 % da ham safe zonada
        x1, cx = x0 + eni, x0 + eni // 2
        fy = self._sh("yorliq", Q.matn.izoh_px)
        while self.yorliq and uzunlik(self.yorliq.upper(), fy) > eni - 48 and fy.size > 36:
            fy = self._sh("yorliq", fy.size - 2)
        rad = 78
        fi = self._sh("yorliq", Q.matn.izoh_px)
        izoh_q = []
        if self.izoh:
            izoh_q = qatorlarga(self.izoh, fi, eni - 30, 0, 2) or [self.izoh]
        h = 36 + (fy.size + 24 if self.yorliq else 0) + 2 * rad + 24 + len(izoh_q) * int(fi.size * 1.15) + 30
        y0 = int(self.markaz_y - h / 2)
        ImageDraw.Draw(g).rounded_rectangle([x0, y0, x1, y0 + h], radius=j["radius"],
                                            fill=rang(r["lower_third"], r["lower_third_alfa"]))
        y = y0 + 36
        if self.yorliq:
            blok_chiz(m, [self.yorliq.upper()], fy, cx, y + fy.size // 2, fy.size)
            y += fy.size + 24
        cy = y + rad
        k = an.ease_out(tt / self.a["vaqt"]["doira_chizish_s"])
        g.alpha_composite(_yoy((cx, cy), rad, 9, k, r["oltin"]))
        f = self._sh("raqam", 150 if len(self.raqam) <= 2 else 90)
        blok_chiz(m, [self.raqam], f, cx, cy, f.size)
        if izoh_q:
            lh = int(fi.size * 1.15)
            blok_chiz(m, izoh_q, fi, cx, cy + rad + 24 + lh * len(izoh_q) / 2, lh)
        return g, m, [(x0, y0, x1, y0 + h)]

    def qatlamlar(self, tt):
        if self.joy == "yon":
            return self._yon(tt)
        r = self.a["ranglar"]
        g, m = _bosh(), _bosh()
        qut, y = self._bosh_qism(m, self.yorliq, self.sarlavha)
        rad = 190
        cy = max(y + rad + 20, Q.th.koz_y + 90)            # sarlavha bo'lmasa ham kompozitsiya markazga yaqin
        k = an.ease_out(tt / self.a["vaqt"]["doira_chizish_s"])
        g.alpha_composite(_yoy((W // 2, cy), rad, 14, k, r["oltin"]))
        f = self._sh("raqam", 230 if len(self.raqam) > 2 else 320)   # bitta belgi (masalan «+») yirikroq
        qut += blok_chiz(m, [self.raqam], f, W // 2, cy, f.size)
        qut.append((W // 2 - rad - 8, cy - rad - 8, W // 2 + rad + 8, cy + rad + 8))
        if self.izoh:
            fi = self._sh("yorliq", Q.matn.izoh_px)
            qut += blok_chiz(m, [self.izoh], fi, W // 2, cy + rad + 70, 60)
        return g, m, qut


KOMPONENTLAR = {
    "LowerThird": LowerThird,
    "RaqamSahna": RaqamSahna,
    "ChecklistSahna": ChecklistSahna,
    "SanaSahna": SanaSahna,
    "DoiraSahna": DoiraSahna,
}
