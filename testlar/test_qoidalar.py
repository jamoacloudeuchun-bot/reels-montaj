"""montaj/qoidalar.py qiymatlari CLAUDE.md matniga mosligini tekshiradi.

CLAUDE.md o'zgartirilmaydi; bu test faqat uni o'qiydi.
"""
import re
from pathlib import Path

from montaj.qoidalar import QOIDALAR as Q

CLAUDE = (Path(__file__).resolve().parent.parent / "CLAUDE.md").read_text(encoding="utf-8")
# Turli tire va minus belgilarini bir xil ko'rinishga keltiramiz
MATN = re.sub(r"[–−]", "-", CLAUDE)


def bor(parcha: str):
    assert parcha in MATN, f"CLAUDE.md da topilmadi: {parcha!r}"


def test_safe_zona():
    bor(f"x {Q.safe.x[0]}-{Q.safe.x[1]}, y {Q.safe.y[0]}-{Q.safe.y[1]}")
    bor(f"720-{Q.safe.markaz_matn_eni_max} px")
    bor(f"~x {Q.safe.yon_kartochka_min_x}")


def test_talking_head():
    bor(f"y {Q.th.hook_y}")
    bor(f"y {Q.th.koz_y}")
    bor(f"y {Q.th.subtitr_y}")
    bor(f"{Q.th.kattalashtirish_foiz[0]}-{Q.th.kattalashtirish_foiz[1]}%")
    bor(f"{Q.th.qoraytirish_kuch} @ {int(Q.th.qoraytirish_balandlik * 100)}%")


def test_matn():
    bor("hamma matn **oq**")
    bor(f"{Q.matn.tracking[0]}…{Q.matn.tracking[1]}")
    bor(f"~{Q.matn.izoh_px} px")
    bor("Sarlavhaga drop shadow qo'yma")
    bor(f"({Q.matn.logotip_plitka_px[0]}-{Q.matn.logotip_plitka_px[1]} px plitka)")
    assert Q.matn.rang == "#FFFFFF" and Q.matn.sarlavha_soya is False


def test_kesish():
    bor(f"boshidan ~{Q.kesish.bosh_zaxira_s} s")
    bor(f"oxiridan ~{Q.kesish.oxir_zaxira_s} s")
    bor(f"{Q.kesish.pauza_min_s} s+ pauzalarni ~{Q.kesish.pauza_qoldiq_s} s")
    bor(f"{Q.kesish.gap_chegara_db:.0f} dB chegarasi")
    bor(f"RMS, {int(Q.kesish.rms_oyna_s * 1000)} ms")
    bor(f"~{Q.kesish.whisper_oldinda_s[0]}-{Q.kesish.whisper_oldinda_s[1]} s oldinda")


def test_ovoz():
    bor(f"`{Q.ovoz.musiqa_db:.0f} dB`")
    bor(f"≈ {Q.ovoz.musiqa_lufs:.0f} LUFS")
    bor(f"Yakuniy {Q.ovoz.yakuniy_lufs:.0f} LUFS")
    bor(f"SFX'ni {Q.ovoz.sfx_gap_ustida_db:.0f} dB")
    bor("(pop, whoosh, hit)")


def test_animatsiya():
    a = Q.anim
    bor(f"pop {a.pop_foiz[0]}→{a.pop_foiz[1]}→{a.pop_foiz[2]}% ({a.pop_s[0]}-{a.pop_s[1]} s)")
    bor(f"~{a.matn_kotarilish_px} px ko'tarilib {a.matn_fade_s} s fade")
    bor(f"Chiqish {a.chiqish_fade_s[0]}-{a.chiqish_fade_s[1]} s fade")
    bor(f"{a.zoom_foiz[0]}→{a.zoom_foiz[1]}-{a.zoom_foiz[2]}%, {a.zoom_kirish_s} s kirish, {a.zoom_chiqish_s} s chiqish")


def test_tasdiq_va_rang():
    bor("Render faqat tasdiqdan keyin")
    bor("Kamera videosi **o'z rangida** qoladi")
    assert Q.render_tasdiqsiz is False and Q.rang_ozgartirish is False
