"""Kesish va gap bo'laklari mantiqi — birinchi videoda qo'lda tasdiqlangan natijalar bilan.

Birinchi video (60 fps, 698 kadr): tasdiqlangan reja — 10–330 va 341–539 kadrlar saqlanadi,
oxiri 540 (exclusive), CapCut ekrani 9.6 s dan keyin olib tashlanadi.
"""
import numpy as np

from montaj.kesish import kesish_rejasi
from montaj.ovoz import birlashtir, gap_bolaklari
from montaj.qabul import oxirgi_ekran

# Birinchi videoning tozalangan ovozidagi xom bo'laklar (o'lchangan)
XOM = [(0.225, 5.45), (5.525, 5.65), (5.75, 8.75), (8.775, 8.925)]


def _db_soxta():
    db = np.full(400, -60.0)
    for a, b, v in [(0.225, 5.45, -9), (5.525, 5.65, -40), (5.75, 8.75, -9), (8.775, 8.925, -33)]:
        db[int(a / 0.025):int(b / 0.025)] = v
    return db


def test_nafas_tashlanadi_va_birlashadi():
    assert birlashtir(XOM, _db_soxta()) == [(0.225, 5.45), (5.75, 8.925)]


def test_qisqa_soz_nafas_deb_tashlanmaydi():
    db = _db_soxta()
    db[int(5.525 / 0.025):int(5.65 / 0.025)] = -12     # baland: bu so'z
    # so'z saqlanadi; atrofidagi uzilishlar < 0.25 s bo'lgani uchun bitta gapga qo'shiladi (kesilmaydi)
    assert birlashtir(XOM, db) == [(0.225, 8.925)]


def test_birinchi_video_rejasi():
    gaplar = birlashtir(XOM, _db_soxta())
    r = kesish_rejasi(gaplar, "60/1", 698, chegara_s=9.6)
    assert r["saqlanadigan_kadrlar"] == [[10, 331], [341, 540]]
    assert r["natija_kadr"] == 520
    assert r["pauzalar"][0]["olib_tashlanadi_kadr"] == [331, 340]
    assert abs(r["pauzalar"][0]["yangi_s"] - 0.133) < 0.002


def test_qisqa_pauza_qisqartirilmaydi():
    r = kesish_rejasi([(1.0, 2.0), (2.2, 3.0)], 30, 300)
    assert r["pauzalar"] == [] and len(r["saqlanadigan_kadrlar"]) == 1


def test_gap_bolaklari():
    db = np.array([-60, -30, -30, -60, -60, -20], float)
    assert gap_bolaklari(db) == [(0.025, 0.075), (0.125, 0.15)]


def test_oxirgi_qora_ekran():
    yorq = np.array([150] * 96 + [17] * 20, float)
    std = np.array([40] * 96 + [5] * 20, float)
    assert oxirgi_ekran(yorq, std, 0.1) == 9.6
    assert oxirgi_ekran(np.full(10, 150.0), np.full(10, 40.0), 0.1) is None
