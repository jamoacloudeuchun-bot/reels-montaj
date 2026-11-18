"""3-bosqich: so'z vaqtlari (faster-whisper) va foydalanuvchi matnini ularga moslash.

CLAUDE.md: Whisper'dan faqat so'z VAQTLARI olinadi; ekrandagi matn — foydalanuvchi tasdiqlagan
matn. Farqlar va noaniq so'zlar hisobotda alohida ko'rsatiladi, hech narsa taxmin bilan
almashtirilmaydi. Vaqtlar ovoz energiyasi (RMS) bo'yicha tuzatiladi.
"""
import json
import os
import re
import unicodedata
from difflib import SequenceMatcher

import numpy as np

from .qoidalar import QOIDALAR

K = QOIDALAR.kesish
MODEL = "large-v3"
NOANIQ_P = 0.5
OXSHASH_MIN = 0.45
LANGAR = 0.75             # shundan yuqori o'xshashlik — so'z aniq mos (langar)
TUZATISH_OYNA_S = 0.45      # Whisper chegarasidan keyin RMS minimumi qidiriladigan oraliq


def normal(soz: str) -> str:
    s = unicodedata.normalize("NFC", soz.lower())
    s = re.sub(r"[‘’ʻʼ`']", "", s)
    s = re.sub(r"[^\w]", "", s)
    return s


def tokenlar(matn: str):
    """Matnni so'zlarga ajratadi; tinish belgilari so'zga yopishgan holda qoladi (ekranda kerak)."""
    return [t for t in matn.split() if normal(t) or t.strip("“”\"«»")]


def whisper_sozlari(audio16k: np.ndarray, til: str, kesh_yol, qayta=False):
    if kesh_yol.exists() and not qayta:
        return json.loads(kesh_yol.read_text(encoding="utf-8"))
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    from faster_whisper import WhisperModel
    m = WhisperModel(MODEL, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(audio16k, language=til, word_timestamps=True, beam_size=5, vad_filter=False)
    sozlar = [{"soz": w.word.strip(), "boshi": round(w.start, 3), "oxiri": round(w.end, 3),
               "p": round(w.probability, 3)} for s in segs for w in s.words]
    kesh_yol.write_text(json.dumps(sozlar, ensure_ascii=False, indent=1), encoding="utf-8")
    return sozlar


def moslash(foyd, whisp):
    """Needleman–Wunsch: foydalanuvchi so'zlari <-> Whisper so'zlari (o'xshashlik bo'yicha).

    Qaytaradi: juftliklar [(i|None, j|None, oxshashlik)].
    """
    a = [normal(t) for t in foyd]
    b = [normal(w["soz"]) for w in whisp]
    n, m = len(a), len(b)
    sim = [[SequenceMatcher(None, x, y).ratio() if x and y else 0 for y in b] for x in a]
    BOSH = -0.4
    D = np.zeros((n + 1, m + 1))
    D[:, 0] = np.arange(n + 1) * BOSH
    D[0, :] = np.arange(m + 1) * BOSH
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = sim[i - 1][j - 1]
            D[i, j] = max(D[i - 1, j - 1] + (s if s >= OXSHASH_MIN else -0.6), D[i - 1, j] + BOSH, D[i, j - 1] + BOSH)
    i, j, juft = n, m, []
    while i > 0 or j > 0:
        if i and j:
            s = sim[i - 1][j - 1]
            if np.isclose(D[i, j], D[i - 1, j - 1] + (s if s >= OXSHASH_MIN else -0.6)):
                juft.append((i - 1, j - 1, s)); i -= 1; j -= 1; continue
        if i and np.isclose(D[i, j], D[i - 1, j] + BOSH):
            juft.append((i - 1, None, 0)); i -= 1
        else:
            juft.append((None, j - 1, 0)); j -= 1
    return juft[::-1]


CHUQURLIK_DB = 10.0        # chegara faqat aniq energiya chuqurligiga suriladi


def _rms_min(db, t0, t1, qadam, asl=None):
    """[t0, t1] dagi RMS minimumi; chuqurlik CHUQURLIK_DB dan kam bo'lsa — asl chegara qoladi."""
    a, b = max(0, int(t0 / qadam)), min(len(db), int(t1 / qadam) + 1)
    if b <= a:
        return t0 if asl is None else asl
    oyna = db[a:b]
    if asl is not None and float(oyna.max() - oyna.min()) < CHUQURLIK_DB:
        return asl
    return (a + int(np.argmin(oyna))) * qadam


def vaqtlarni_qur(foyd, whisp, juft, db, gaplar, qadam=K.rms_oyna_s):
    """Foydalanuvchi so'zlariga vaqt beradi: mos Whisper so'zidan, bo'lmasa interpolyatsiya.

    Tuzatish: so'zlar orasidagi chegara Whisper chegarasidan keyingi TUZATISH_OYNA_S ichidagi
    RMS minimumiga suriladi (Whisper oldinda chiqadi); boshlanish/tugash gap bo'laklariga tortiladi.
    """
    n = len(foyd)
    boshi, oxiri, manba, mos_p = [None] * n, [None] * n, ["taqsimlangan"] * n, [None] * n
    jami_boshi = gaplar[0][0] if gaplar else (whisp[0]["boshi"] if whisp else 0)
    jami_oxiri = gaplar[-1][1] if gaplar else (whisp[-1]["oxiri"] if whisp else 0)

    # 1) Langarlar: aniq mos juftliklar (o'xshashlik >= LANGAR) — so'z Whisper vaqtini oladi.
    # 2) Langarlar orasidagi guruh: Whisper so'zlarining umumiy oralig'i foydalanuvchi so'zlariga
    #    harf uzunligiga mutanosib taqsimlanadi (bitta eshitilgan so'z bir nechta yozilgan so'zga
    #    to'g'ri kelishi mumkin: "oligaxlarga" ≈ "oliy ta'lim muassasalariga").
    guruh_u, guruh_w = [], []

    def guruhni_yop(t0, t1):
        if not guruh_u:
            guruh_w.clear(); return
        if guruh_w:
            t0 = min(whisp[j]["boshi"] for j in guruh_w) if t0 is None else max(t0, min(whisp[j]["boshi"] for j in guruh_w))
            t1 = max(whisp[j]["oxiri"] for j in guruh_w) if t1 is None else t1
        t0 = jami_boshi if t0 is None else t0
        t1 = jami_oxiri if t1 is None else t1
        uz = [max(1, len(normal(foyd[k]))) for k in guruh_u]
        t, jami = t0, sum(uz)
        for k, u in zip(guruh_u, uz):
            boshi[k] = t; t += (t1 - t0) * u / jami; oxiri[k] = t
            if guruh_w:
                mos_p[k] = min(whisp[j]["p"] for j in guruh_w)
        guruh_u.clear(); guruh_w.clear()

    oldingi_oxir = None
    for i, j, s in juft:
        if i is not None and j is not None and s >= LANGAR:
            w = whisp[j]
            guruhni_yop(oldingi_oxir, w["boshi"])
            boshi[i], oxiri[i], manba[i], mos_p[i] = w["boshi"], w["oxiri"], "whisper", w["p"]
            oldingi_oxir = w["oxiri"]
        else:
            if i is not None:
                guruh_u.append(i)
            if j is not None:
                guruh_w.append(j)
    guruhni_yop(oldingi_oxir, None)

    # 3) RMS bo'yicha chegaralarni tuzatish (Whisper oldinda chiqadi). Har so'z kamida yarmini saqlaydi.
    b0, o0 = list(boshi), list(oxiri)          # tuzatishdan oldingi vaqtlar (zanjirli siljish bo'lmasin)
    for k in range(n - 1):
        chegara = oxiri[k]
        past = max(boshi[k] + 0.03, b0[k] + 0.5 * (o0[k] - b0[k]))
        yuqori = min(chegara + TUZATISH_OYNA_S, b0[k + 1] + 0.5 * (o0[k + 1] - b0[k + 1]))
        yangi = _rms_min(db, max(past, chegara - 0.05), yuqori, qadam, asl=chegara) if yuqori > past else chegara
        oxiri[k] = boshi[k + 1] = round(yangi, 3)
    if gaplar:
        boshi[0] = min((g[0] for g in gaplar if g[1] > boshi[0]), key=lambda g0: abs(g0 - boshi[0]), default=boshi[0])
        oxiri[-1] = min((g[1] for g in gaplar), key=lambda g1: abs(g1 - oxiri[-1]))
    return [{"soz": foyd[k], "boshi": round(boshi[k], 3), "oxiri": round(oxiri[k], 3),
             "manba": manba[k], "p": mos_p[k]} for k in range(n)]


def farqlar(foyd, whisp, juft):
    """Foydalanuvchi matni va eshitilgan so'zlar orasidagi farqlar (bo'laklab)."""
    natija, joriy = [], None
    for i, j, s in juft:
        mos = i is not None and j is not None and s >= LANGAR
        if mos:
            if joriy:
                natija.append(joriy); joriy = None
            continue
        joriy = joriy or {"matnda": [], "eshitildi": [], "boshi": None, "oxiri": None, "p_min": 1.0}
        if i is not None:
            joriy["matnda"].append(foyd[i])
        if j is not None:
            w = whisp[j]
            joriy["eshitildi"].append(w["soz"])
            joriy["boshi"] = w["boshi"] if joriy["boshi"] is None else joriy["boshi"]
            joriy["oxiri"] = w["oxiri"]
            joriy["p_min"] = min(joriy["p_min"], w["p"])
    if joriy:
        natija.append(joriy)
    for f in natija:
        f["matnda"], f["eshitildi"] = " ".join(f["matnda"]), " ".join(f["eshitildi"])
    return natija


def matn_bosqichi(lo, ovoz, qayta=False) -> dict:
    from .ovoz import audio_oqi
    gacha = ovoz.get("gacha_s")
    a16 = audio_oqi(lo.video, 16000, gacha)
    whisp = whisper_sozlari(a16, lo.til, lo.kesh / "whisper_sozlar.json", qayta)
    foyd = tokenlar(lo.matn)
    juft = moslash(foyd, whisp)
    sozlar = vaqtlarni_qur(foyd, whisp, juft, ovoz["rms_db"], ovoz["gap_bolaklari"])
    return {
        "eshitilgan_xom": " ".join(w["soz"] for w in whisp),
        "sozlar": sozlar,
        "farqlar": farqlar(foyd, whisp, juft),
        "noaniq": [w for w in whisp if w["p"] < NOANIQ_P],
        "mos_ulush": round(sum(1 for s in sozlar if s["manba"] == "whisper") / max(1, len(sozlar)), 2),
    }
