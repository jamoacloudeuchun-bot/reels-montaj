"""Subtitr bo'laklari va hook vaqti.

Qoidalar:
- Subtitr matni = foydalanuvchi tasdiqlagan matn (so'zlar tartibi va yozilishi o'zgarmaydi).
- "Bir so'z bir vaqtda faqat bitta joyda": hook ekranda turganda hook'dagi so'zlar aytilayotgan
  qism subtitrda ko'rsatilmaydi. Hook o'sha so'zlar aytilib bo'lguncha turadi (HOOK_MAX_S gacha).
"""
from .grafika.shrift import qatorlarga, shrift
from .matn import normal

HOOK_MIN_S = 1.5
HOOK_MAX_S = 5.0
OZAK = 5                        # so'z o'zagi: birinchi 5 harf (qo'shimchalarni e'tiborsiz qoldirish uchun)
TINISH = ",.!?;:"


def _ozak(soz):
    n = normal(soz)
    return n[:OZAK] if len(n) >= 4 else None


def hook_tugashi(sozlar, hook: str | None):
    """Hook'dagi so'zlar aytiladigan oxirgi so'z indeksi (manba vaqti bo'yicha HOOK_MAX_S ichida)."""
    if not hook or not sozlar:
        return -1
    ozaklar = {o for o in (_ozak(w) for w in hook.split()) if o}
    t0 = sozlar[0]["boshi"]
    oxirgi = -1
    for i, s in enumerate(sozlar):
        if s["boshi"] - t0 > HOOK_MAX_S:
            break
        if _ozak(s["soz"]) in ozaklar:
            oxirgi = i
    return oxirgi


def bolaklar(sozlar, uslub, boshlash: int = 0):
    """So'zlarni subtitr bo'laklariga ajratadi: avval tinish belgisida, sig'masa teng bo'laklarga."""
    sh = uslub["shrift"]["subtitr"]
    f = shrift(sh["fayl"], uslub["olcham_px"]["subtitr"], sh["vazn"])
    eni = uslub.get("eni_px", {}).get("subtitr", 760)
    qmax = uslub.get("subtitr_qator_max", 3)

    gaplar, joriy = [], []
    for i in range(boshlash, len(sozlar)):
        joriy.append(i)
        if sozlar[i]["soz"][-1] in TINISH:
            gaplar.append(joriy); joriy = []
    if joriy:
        gaplar.append(joriy)

    natija = []
    for g in gaplar:
        for k in range(1, len(g) + 1):                       # eng kam bo'lakka bo'lish
            qism = [g[round(j * len(g) / k):round((j + 1) * len(g) / k)] for j in range(k)]
            if all(qatorlarga(" ".join(sozlar[x]["soz"] for x in q), f, eni, 0, qmax) for q in qism):
                natija += qism
                break
    return [{"sozlar": q, "matn": " ".join(sozlar[x]["soz"] for x in q),
             "boshi": sozlar[q[0]]["boshi"], "oxiri": sozlar[q[-1]]["oxiri"]} for q in natija]


def jadval(sozlar, uslub, hook: str | None):
    """Qaytaradi: (hook_oraliq_manba | None, subtitr bo'laklari) — vaqtlar MANBA videosi bo'yicha.

    Bo'laklar uzluksiz: har biri keyingisi boshlanguncha turadi (miltillash bo'lmasin).
    """
    h = hook_tugashi(sozlar, hook)
    bosh = h + 1
    b = bolaklar(sozlar, uslub, bosh)
    for x, y in zip(b, b[1:]):
        x["oxiri"] = y["boshi"]
    hook_oraliq = None
    if hook:
        oxir = sozlar[bosh]["boshi"] if bosh < len(sozlar) else sozlar[-1]["oxiri"]
        hook_oraliq = (sozlar[0]["boshi"], max(oxir, sozlar[0]["boshi"] + HOOK_MIN_S))
    return hook_oraliq, b
