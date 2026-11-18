import json

import pytest
from PIL import ImageFont

from montaj.loyiha import SozlamaXatosi, loyiha_yukla, shrift_yoli, uslub_yukla


def _yoz(papka, d):
    (papka / "loyiha.json").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return papka


def test_loyiha_yuklanadi(tmp_path):
    lo = loyiha_yukla(_yoz(tmp_path, {"nom": "t", "video": "/yoq.mov", "matn": "  Salom  "}))
    assert lo.matn == "Salom" and lo.uslub_nomi == "asosiy" and lo.hook is None and lo.til == "uz"


def test_majburiy_maydon(tmp_path):
    with pytest.raises(SozlamaXatosi, match="matn"):
        loyiha_yukla(_yoz(tmp_path, {"nom": "t", "video": "/v.mov"}))


def test_noma_lum_uslub():
    with pytest.raises(SozlamaXatosi, match="uslub topilmadi"):
        uslub_yukla("bunday_uslub_yoq")


def test_asosiy_uslub_shriftlari_ozbekcha():
    us = uslub_yukla("asosiy")
    for rol, s in us["shrift"].items():
        yol = shrift_yoli(s["fayl"])
        assert yol.exists(), f"{rol}: shrift yo'q: {yol}"
        f = ImageFont.truetype(str(yol), 80)
        if s.get("vazn"):
            f.set_variation_by_name(s["vazn"])
        bosh = bytes(f.getmask(""))
        for c in "O‘G‘o‘g‘’ЎўҚқҒғҲҳ":
            assert bytes(f.getmask(c)) != bosh, f"{rol}: {c!r} belgisi yo'q"


def test_asosiy_uslubda_oqdan_boshqa_matn_rangi_yoq():
    matn = json.dumps(uslub_yukla("asosiy"))
    assert "#" not in matn.replace('"_papka"', ""), "asosiy uslubda rang kodi bo'lmasligi kerak (matn oq)"
