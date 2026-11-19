"""B5: Andoza_01 uslub paketi — yadrodan ajratilganlik, CLAUDE.md qoidalari, safe zona, sintetik video."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from montaj.loyiha import ILDIZ, loyiha_yukla, uslub_yukla
from montaj.sahna import Sahna, _komponentlar, safe_tekshir, sahna_qur

US = uslub_yukla("andoza_01")
K = _komponentlar(US)
OLTIN = (0xE6, 0xAD, 0x49)

NAMUNA = {
    "RaqamSahna": dict(raqam="4–7", yorliq="1-komponent", sarlavha="RAQAM VA SHKALA", birlik="qadam",
                       izoh="izoh matni", shkala=[1, 10], qiymat=[4, 7]),
    "LowerThird": dict(matn="Kartochka", yorliq="2-komponent", ikonka="odam"),
    "ChecklistSahna": dict(bandlar=["Birinchi band", "Ikkinchi band", "Uchinchi band", "To‘rtinchi band"],
                           yorliq="3-komponent", sarlavha="RO‘YXAT SARLAVHASI UZUN BO‘LSA HAM", belgilangan=[0, 2]),
    "SanaSahna": dict(sanalar=[{"oy": "yanvar", "kun": "12", "izoh": "a"}, {"oy": "fevral", "kun": "28"},
                               {"oy": "mart", "kun": "3", "izoh": "c"}], yorliq="4-komponent", sarlavha="SANALAR"),
    "DoiraSahna": dict(raqam="5", yorliq="5-komponent", sarlavha="DOIRA", izoh="izoh"),
}


def _el(nom, boshi=0.0, oxiri=3.0, **qosh):
    return K[nom](boshi, oxiri, uslub=US, **{**NAMUNA[nom], **qosh})


def test_paket_alohida_va_yadro_uni_bilmaydi():
    assert set(NAMUNA) <= set(K)
    assert "komponentlar" not in uslub_yukla("asosiy")          # asosiy uslubga hech narsa qo'shilmagan
    yadro = "".join(p.read_text(encoding="utf-8") for p in (ILDIZ / "montaj").rglob("*.py")).lower()
    assert "andoza_01" not in yadro and "uslublar/andoza" not in yadro


def test_referencesga_tegilmagan():
    import subprocess
    r = subprocess.run(["git", "status", "--porcelain", "REFERENCES", "CLAUDE.md"], cwd=ILDIZ,
                       capture_output=True, text=True)
    assert r.stdout.strip() == ""


@pytest.mark.parametrize("nom", list(NAMUNA))
def test_matn_faqat_oq_oltin_faqat_grafikada(nom):
    e = _el(nom)
    g, m, _ = e.qatlamlar(2.5)
    mm = np.asarray(m)
    rangi = mm[mm[..., 3] > 0][:, :3]
    assert len(rangi) > 300 and (rangi == 255).all(), "matn qatlamida faqat oq piksellar bo'lishi kerak"
    gg = np.asarray(g)
    oltin = (np.abs(gg[..., :3].astype(int) - OLTIN).sum(-1) < 12) & (gg[..., 3] > 200)
    if nom in ("LowerThird", "ChecklistSahna", "RaqamSahna", "DoiraSahna", "SanaSahna"):
        assert oltin.any(), "oltin grafik element (ikonka/✓/chiziq) bo'lishi kerak"


@pytest.mark.parametrize("nom", list(NAMUNA))
def test_safe_zona_butun_animatsiya_davomida(nom):
    e = _el(nom)
    assert safe_tekshir(Sahna([e], 3.0, "30/1", [(0, 90)]), qadam_s=1 / 60) == []


def test_tracking_va_soyasiz():
    assert 0 <= US["tracking"]["yorliq"] <= 20 and 0 <= US["tracking"]["sarlavha"] <= 20
    assert "soya" not in json.dumps(US["andoza"])


def test_kirish_animatsiyasi_pop_va_chiqish_fade():
    from montaj.grafika import animatsiya as an
    e = _el("LowerThird", 0, 2)
    from PIL import Image
    def alfa(t):
        q = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); e.chiz(t, q)
        return int(np.asarray(q)[..., 3].max())
    assert alfa(0.0) < 30 and alfa(0.5) == 255 and alfa(1.95) < 100     # 0.1 s kirish, 0.25 s chiqish
    assert an.pop_shkala(an.POP_CHOQQI_S) == pytest.approx(1.06)


def test_checklist_bandlari_birin_ketin():
    e = _el("ChecklistSahna")
    v = US["andoza"]["vaqt"]
    _, _, q0 = e.qatlamlar(0.05)
    _, _, q2 = e.qatlamlar(v["band_oraligi_s"] * 2 + 0.05)
    assert len(q2) - len(q0) == 2


def test_xato_holatlar():
    with pytest.raises(ValueError, match="sig'maydi"):
        _el("ChecklistSahna", bandlar=[f"band {i}" for i in range(9)]).qatlamlar(5)
    with pytest.raises(ValueError, match="1–3"):
        _el("SanaSahna", sanalar=[]).qatlamlar(1)


def test_grafika_subtitrni_yashiradi_va_soz_boyicha_vaqt():
    sozlar = [{"soz": s, "boshi": i * 0.5, "oxiri": (i + 1) * 0.5} for i, s in enumerate("bir ikki uch tort besh olti".split())]
    lo = SimpleNamespace(hook=None, grafikalar=[{"tur": "LowerThird", "soz": "uch", "davom_s": 1.0, **NAMUNA["LowerThird"]}])
    s = sahna_qur(lo, US, {"sozlar": sozlar}, {"fps": "30/1", "saqlanadigan_kadrlar": [[0, 90]], "natija_kadr": 90})
    lt = next(e for e in s.elementlar if type(e).__name__ == "LowerThird")
    assert lt.boshi == 1.0 and lt.oxiri == 2.0
    _, q = s.qatlam(1.5)
    assert not any(type(e).__name__ == "Subtitr" for e, _ in q)            # bir so'z bir joyda
    _, q = s.qatlam(2.5)
    assert any(type(e).__name__ == "Subtitr" for e, _ in q)


def test_nomalum_tur():
    lo = SimpleNamespace(hook=None, grafikalar=[{"tur": "YoqKomponent", "boshi_s": 0}])
    with pytest.raises(ValueError, match="noma'lum grafika turi"):
        sahna_qur(lo, US, {"sozlar": [{"soz": "a", "boshi": 0, "oxiri": 1}]},
                  {"fps": "30/1", "saqlanadigan_kadrlar": [[0, 30]], "natija_kadr": 30})


def _namuna_moduli():
    spec = importlib.util.spec_from_file_location("namuna", ILDIZ / "uslublar" / "andoza_01" / "namuna.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_sintetik_video_tolik_yol(tmp_path):
    """Sintetik loyiha: sahna -> safe zona -> render yo'li kadrlari -> sintetik render + avtomatik tekshiruv."""
    from montaj.bosqichlar import _matn_kesish
    from montaj.ovoz_miks import ovoz_tayyorla
    from montaj.render import kadrlar_render_yolida, render, tekshir
    papka = _namuna_moduli().yarat(tmp_path / "namuna", dav=8.0)
    lo = loyiha_yukla(papka)
    mt, kn = _matn_kesish(lo)
    sahna = sahna_qur(lo, US, mt, kn)
    assert safe_tekshir(sahna) == []
    k = kadrlar_render_yolida(lo, sahna, [1.0, 2.6, 4.2], tmp_path)
    assert len(k) == 3 and all(Path(x).exists() for x in k)
    ov = ovoz_tayyorla(lo, kn, sahna, lo.kesh / "ovoz_tozalangan.wav")
    chiq = render(lo, sahna, ov["fayl"], tmp_path / "s.mp4", tasdiq=True)
    t = tekshir(lo, sahna, chiq)
    assert t["holat"] == "OK", t["xatolar"]


def test_komponent_izoh_parametri_yoqolmaydi():
    """loyiha.json dagi "_izoh" — fayl izohi; "izoh" — komponent parametri (oldin adashib o'chirilardi)."""
    lo = SimpleNamespace(hook=None, grafikalar=[{"tur": "DoiraSahna", "boshi_s": 0, "davom_s": 1, "raqam": "+",
                                                 "izoh": "belgisini qoldiring", "_izoh": "fayl uchun izoh"}])
    s = sahna_qur(lo, US, {"sozlar": [{"soz": "a", "boshi": 0, "oxiri": 1}]},
                  {"fps": "30/1", "saqlanadigan_kadrlar": [[0, 30]], "natija_kadr": 30})
    d = next(e for e in s.elementlar if type(e).__name__ == "DoiraSahna")
    assert d.izoh == "belgisini qoldiring"
