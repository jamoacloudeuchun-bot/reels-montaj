import numpy as np

from montaj.matn import farqlar, moslash, normal, tokenlar, vaqtlarni_qur


def test_normal_apostrof_va_belgilar():
    assert normal("Qo‘llanma,") == normal("qollanma") == "qollanma"
    assert normal("ta’lim") == normal("taʼlim") == "talim"


def test_tokenlar_plyus_belgisi_saqlanadi():
    t = tokenlar("kommentariyada “+” belgisini qoldiring.")
    assert t == ["kommentariyada", "“+”", "belgisini", "qoldiring."]


W = [{"soz": s, "boshi": a, "oxiri": b, "p": p} for s, a, b, p in [
    ("Agar", 0.0, 0.48, 0.56), ("sizxam", 0.48, 0.94, 0.6), ("xarbi", 0.94, 1.52, 0.77),
    ("oligaxlarga", 1.52, 2.48, 0.71), ("kirish", 2.48, 2.92, 0.75)]]


def test_moslash_va_farqlar():
    foyd = tokenlar("Agar siz ham harbiy oliy ta’lim muassasalariga kirish")
    juft = moslash(foyd, W)
    mos = {foyd[i]: W[j]["soz"] for i, j, s in juft if i is not None and j is not None and s >= 0.45}
    assert mos["Agar"] == "Agar" and mos["harbiy"] == "xarbi" and mos["kirish"] == "kirish"
    f = farqlar(foyd, W, juft)
    assert any("muassasalariga" in x["matnda"] for x in f)     # farq ko'rsatiladi, almashtirilmaydi


def test_vaqtlar_tartibli_va_matn_ozgarmaydi():
    foyd = tokenlar("Agar siz ham harbiy oliy ta’lim muassasalariga kirish")
    db = np.full(200, -10.0)
    s = vaqtlarni_qur(foyd, W, moslash(foyd, W), db, [(0.225, 2.9)])
    assert [x["soz"] for x in s] == foyd                      # foydalanuvchi matni aynan saqlanadi
    assert s[0]["boshi"] == 0.225 and s[-1]["oxiri"] == 2.9
    assert all(a["oxiri"] <= b["boshi"] + 1e-9 for a, b in zip(s, s[1:]))
    assert all(x["boshi"] < x["oxiri"] for x in s)


def test_tekis_energiyada_chegara_surilmaydi():
    from montaj.matn import _rms_min
    db = np.full(100, -10.0)
    db[40] = -14                                   # 4 dB — haqiqiy pauza emas
    assert _rms_min(db, 0.5, 1.2, 0.025, asl=0.6) == 0.6
    db[40] = -40                                   # 30 dB chuqurlik — pauza
    assert _rms_min(db, 0.5, 1.2, 0.025, asl=0.6) == 1.0


def test_qolda_vaqt_chegarani_suradi():
    from montaj.matn import qolda_vaqtlar
    s = [{"soz": "qoldiring.", "boshi": 7.0, "oxiri": 7.36, "manba": "w"},
         {"soz": "Biz", "boshi": 7.36, "oxiri": 7.6, "manba": "w"}]
    r = qolda_vaqtlar(s, [{"soz": "biz", "boshi": 7.5}])
    assert r[0]["oxiri"] == 7.5 and r[1]["boshi"] == 7.5 and r[1]["manba"] == "foydalanuvchi_chegarasi" and r[1]["tasdiq"] == "faqat_boshi"


def test_qolda_vaqt_notogri_bolsa_xato():
    import pytest
    from montaj.matn import qolda_vaqtlar
    s = [{"soz": "a", "boshi": 0, "oxiri": 1, "manba": "w"}, {"soz": "b", "boshi": 1, "oxiri": 2, "manba": "w"}]
    with pytest.raises(ValueError):
        qolda_vaqtlar(s, [{"soz": "b", "boshi": 5}])


def test_qolda_vaqt_keyingi_sozlarni_qayta_taqsimlaydi():
    from montaj.matn import qolda_vaqtlar
    s = [{"soz": w, "boshi": a, "oxiri": b, "manba": "w"} for w, a, b in
         [("qoldiring.", 7.03, 7.36), ("Biz", 7.36, 7.50), ("sizga", 7.50, 7.80), ("maxsus", 7.80, 8.07)]]
    r = qolda_vaqtlar(s, [{"soz": "Biz", "boshi": 7.58}])
    assert [x["soz"] for x in r] == ["qoldiring.", "Biz", "sizga", "maxsus"]       # matn o'zgarmaydi
    assert r[0]["oxiri"] == r[1]["boshi"] == 7.58
    assert r[1]["oxiri"] == r[2]["boshi"] and r[2]["oxiri"] == 7.80 and r[3]["boshi"] == 7.80
    assert all(x["oxiri"] - x["boshi"] >= 0.08 for x in r)
    assert r[1]["tasdiq"] == "faqat_boshi" and r[2]["tasdiq"] == "yoq"           # ichki vaqtlar tasdiqlanmagan
