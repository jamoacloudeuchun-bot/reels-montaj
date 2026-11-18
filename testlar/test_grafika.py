"""B3: subtitr bo'laklari, hook vaqti, animatsiya egri chiziqlari, safe zona va oq matn."""
import numpy as np
import pytest
from PIL import Image

from montaj.grafika import animatsiya as an
from montaj.grafika.elementlar import Hook, Kartochka, Royxat, Subtitr
from montaj.loyiha import uslub_yukla
from montaj.qoidalar import QOIDALAR as Q
from montaj.sahna import Sahna, manba_vaqti_natijaga, safe_tekshir
from montaj.subtitr import hook_tugashi, jadval

US = uslub_yukla("asosiy")
MATN = ("Agar siz ham harbiy oliy ta’lim muassasalariga kirish bo‘yicha qo‘llanmaga ega bo‘lishni "
        "istasangiz, kommentariyada “+” belgisini qoldiring. Biz sizga maxsus qo‘llanmani taqdim etamiz!")
HOOK = "HARBIY OLIY TA’LIMGA KIRISH QO‘LLANMASI"


def _sozlar():
    w = MATN.split()
    return [{"soz": s, "boshi": 0.2 + 0.37 * i, "oxiri": 0.2 + 0.37 * (i + 1)} for i, s in enumerate(w)]


def test_hook_soz_ozaklari_bilan_tugaydi():
    s = _sozlar()
    assert s[hook_tugashi(s, HOOK)]["soz"] == "qo‘llanmaga"
    assert hook_tugashi(s, None) == -1


def test_subtitr_bolaklari_va_matn_saqlanadi():
    hook_or, b = jadval(_sozlar(), US, HOOK)
    assert [x["matn"] for x in b] == ["ega bo‘lishni istasangiz,", "kommentariyada “+” belgisini qoldiring.",
                                      "Biz sizga maxsus qo‘llanmani taqdim etamiz!"]
    assert hook_or[1] == b[0]["boshi"]                         # hook va subtitr bir vaqtda emas
    assert all(x["oxiri"] == y["boshi"] for x, y in zip(b, b[1:]))   # uzluksiz


def test_hooksiz_hamma_matn_subtitrda():
    _, b = jadval(_sozlar(), US, None)
    assert " ".join(x["matn"] for x in b) == MATN


def test_pop_egri_chizigi():
    assert an.pop_shkala(0) == pytest.approx(0.80)
    assert an.pop_shkala(an.POP_CHOQQI_S) == pytest.approx(1.06)
    assert an.pop_shkala(an.POP_S) == pytest.approx(1.00)
    assert Q.anim.pop_s[0] <= an.POP_S <= Q.anim.pop_s[1]
    assert Q.anim.chiqish_fade_s[0] <= an.CHIQISH_S <= Q.anim.chiqish_fade_s[1]


def test_matn_kotarilishi_va_zoom():
    assert an.kirish_kotarilish(0) == (36, 0)
    assert an.kirish_kotarilish(0.2) == (0, 1)
    assert an.zoom_zarba(0.3) == pytest.approx(1.10)
    assert an.zoom_zarba(0.65) == pytest.approx(1.0)


def _sahna(el, dav=6.0):
    return Sahna(el, dav, "30/1", [(0, int(dav * 30))])


def test_safe_zona_hamma_elementlar_animatsiya_bilan():
    el = [Hook(0, 2, HOOK, US), Subtitr(2, 4, "Biz sizga maxsus qo‘llanmani taqdim etamiz!", US),
          Kartochka(4, 5, "O‘G‘IL BOLALAR", "faqatgina", US),
          Royxat(5, 6, "QABUL BOSQICHLARI", ["Dastlabki tanlov", "Kasbiy tanlov", "Test sinovlari"], US)]
    assert safe_tekshir(_sahna(el)) == []


def test_safe_tekshiruv_buzilishni_ushlaydi():
    k = Kartochka(0, 1, "UZUN", None, US, x0=40, x1=1000)
    xato = safe_tekshir(_sahna([k], 1.0))
    assert xato and xato[0]["sabab"] == "safe zonadan tashqarida"


def test_matn_faqat_oq_va_soyasiz():
    q = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    u = dict(US, qoraytirish={"pastki_gradient": False, "sarlavha_ortida": None, "subtitr_ortida": None})
    Hook(0, 2, HOOK, u).chiz(1.0, q)
    Subtitr(0, 2, "o‘g‘il “+” ta’lim", u).chiz(1.0, q)
    a = np.asarray(q)
    rang = a[a[..., 3] > 0][:, :3]
    assert len(rang) > 1000 and (rang == 255).all(), "matn piksellari faqat oq bo'lishi kerak (soya yo'q)"


def test_manba_vaqti_natijaga():
    orl = [(10, 331), (341, 540)]
    assert manba_vaqti_natijaga(10 / 60, orl, 60) == 0
    assert manba_vaqti_natijaga(5.6, orl, 60) == pytest.approx(321 / 60)     # kesilgan joy -> keyingi bo'lak
    assert manba_vaqti_natijaga(9.5, orl, 60) == pytest.approx(520 / 60)


def _opacity(el, t):
    q = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    u = dict(US, qoraytirish={"pastki_gradient": False, "sarlavha_ortida": None, "subtitr_ortida": None})
    el.uslub = u
    el.chiz(t, q)
    return int(np.asarray(q)[..., 3].max())


def test_ketma_ket_subtitr_almashuvgacha_toliq_korinadi():
    from montaj.sahna import sahna_qur
    from types import SimpleNamespace
    sozlar = _sozlar()
    lo = SimpleNamespace(hook=HOOK)
    n = len(sozlar) * 0.37 + 0.3
    sahna = sahna_qur(lo, US, {"sozlar": sozlar}, {"fps": "30/1", "saqlanadigan_kadrlar": [[0, int(n * 30)]],
                                                   "natija_kadr": int(n * 30)})
    sub = [e for e in sahna.elementlar if type(e).__name__ == "Subtitr"]
    assert [e.chiqish_s for e in sub] == [0.0, 0.0, 0.2]                    # fade faqat oxirgisida
    for a, b in zip(sub, sub[1:]):
        assert a.oxiri == b.boshi
        assert _opacity(a, a.oxiri - 0.01) == 255                            # almashuvgacha to'liq
        assert _opacity(b, b.boshi + 0.001) < 20 and _opacity(b, b.boshi + 0.2) == 255   # 0.2 s kirish
    assert _opacity(sub[-1], sub[-1].oxiri - 0.1) < 200                      # oxirgisi so'nadi
    hook = next(e for e in sahna.elementlar if type(e).__name__ == "Hook")
    assert hook.oxiri == sub[0].boshi
