"""4-bosqich: kadr raqamli kesish rejasi.

CLAUDE.md:
- gap boshidan ~0.05 s, oxiridan ~0.08 s qoldiriladi;
- ichki 0.25 s+ pauzalar ~0.12 s ga qisqartiriladi;
- kesimlar kadr raqami bilan.
Kadrlar [boshi, oxiri) — oxiri kirmaydi.
"""
from .qoidalar import QOIDALAR
from .vaqt import fps_qiymat, kadr_vaqti, kadrga, oraliqlar_uzunligi

K = QOIDALAR.kesish


def kesish_rejasi(gaplar, fps, jami_kadr, chegara_s=None) -> dict:
    """gaplar: birlashtirilgan gap bo'laklari [(boshi_s, oxiri_s)], vaqt bo'yicha tartiblangan.

    chegara_s: shu vaqtdan keyingi qism (masalan oxirgi logotip ekrani) albatta tashlanadi.
    """
    if not gaplar:
        raise ValueError("gap bo'laklari topilmadi")
    fps = fps_qiymat(fps)
    maks = jami_kadr if chegara_s is None else min(jami_kadr, kadrga(chegara_s, fps, "past"))
    boshi = max(0, kadrga(gaplar[0][0] - K.bosh_zaxira_s, fps, "past"))
    oxiri = min(maks, kadrga(gaplar[-1][1] + K.oxir_zaxira_s, fps))
    yarim = K.pauza_qoldiq_s / 2

    olib_tashlash, pauzalar = [], []
    for (a0, a1), (b0, b1) in zip(gaplar, gaplar[1:]):
        pauza = b0 - a1
        if pauza >= K.pauza_min_s:
            k0, k1 = kadrga(a1 + yarim, fps), kadrga(b0 - yarim, fps)
            if k1 > k0:
                olib_tashlash.append((k0, k1))
                pauzalar.append({"oraliq_s": [round(a1, 3), round(b0, 3)], "asl_s": round(pauza, 3),
                                 "yangi_s": round(pauza - (k1 - k0) / float(fps), 3),
                                 "olib_tashlanadi_kadr": [k0, k1 - 1]})

    saqlash, joriy = [], boshi
    for k0, k1 in olib_tashlash:
        if k0 > joriy:
            saqlash.append((joriy, k0))
        joriy = max(joriy, k1)
    if oxiri > joriy:
        saqlash.append((joriy, oxiri))

    jami = oraliqlar_uzunligi(saqlash)
    return {
        "fps": str(fps),
        "saqlanadigan_kadrlar": [[a, b] for a, b in saqlash],      # [boshi, oxiri)
        "saqlanadigan_vaqt_s": [[round(kadr_vaqti(a, fps), 4), round(kadr_vaqti(b, fps), 4)] for a, b in saqlash],
        "boshi_kadr": boshi, "oxiri_kadr_exclusive": oxiri,
        "pauzalar": pauzalar,
        "natija_kadr": jami,
        "natija_s": round(jami / float(fps), 3),
        "olib_tashlangan_oxir_s": None if chegara_s is None else round(chegara_s, 3),
    }
