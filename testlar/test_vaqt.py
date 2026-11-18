from fractions import Fraction

from montaj.vaqt import fps_qiymat, kadr_vaqti, kadrga, manbadan_natijaga, oraliqlar_uzunligi


def test_fps():
    assert fps_qiymat("60/1") == 60
    assert fps_qiymat("30000/1001") == Fraction(30000, 1001)
    assert fps_qiymat(29.97) == Fraction(30000, 1001)


def test_kadrga_usullar():
    assert kadrga(0.175, 60, "past") == 10
    assert kadrga(5.51, 60) == 331
    assert kadrga(9.005, 60) == 540
    assert kadrga(1 / 60 * 7, 60, "yuqori") == 7   # suzuvchi nuqta xatosiga chidamli
    assert kadr_vaqti(540, "60/1") == 9.0


def test_oraliq_xaritasi():
    oraliq = [(10, 331), (341, 540)]
    assert oraliqlar_uzunligi(oraliq) == 520
    assert manbadan_natijaga(10 / 60, oraliq, 60) == 0
    assert manbadan_natijaga(5.6, oraliq, 60) is None                 # olib tashlangan joy
    assert abs(manbadan_natijaga(341 / 60, oraliq, 60) - 321 / 60) < 1e-9
