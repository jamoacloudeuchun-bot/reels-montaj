"""Birinchi loyiha bo'yicha to'liq tahlil (video va modellar bo'lsa). Ishga tushirish: pytest -m sekin"""
import pytest

from montaj.loyiha import loyiha_yukla

pytestmark = pytest.mark.sekin


def test_birinchi_video_tahlili():
    lo = loyiha_yukla("harbiy_qollanma")
    if not lo.video.exists():
        pytest.skip("birinchi video bu muhitda yo'q")
    from montaj.bosqichlar import ishga_tushir
    n = ishga_tushir("tahlil", lo)
    assert n["qabul"]["oxirgi_qora_ekran_s"] == pytest.approx(9.6, abs=0.1)
    assert n["kesish"]["saqlanadigan_kadrlar"] == [[10, 331], [341, 540]]
    s = n["matn"]["sozlar"]
    assert " ".join(x["soz"] for x in s) == lo.matn            # matn aynan saqlanadi
    assert min(x["oxiri"] - x["boshi"] for x in s) >= 0.08
