"""2-bosqich: ovozni tozalash (DeepFilterNet) va gap bo'laklarini topish (RMS, 25 ms, -42 dB)."""
import subprocess
import sys
import types
from pathlib import Path

import numpy as np

from .qoidalar import QOIDALAR

K = QOIDALAR.kesish
NAFAS_MAX_S = 0.15     # pauza ichidagi shundan qisqa bo'lak nafas/shovqin hisoblanadi (taxmin)


def audio_oqi(video, sr: int, gacha_s: float | None = None) -> np.ndarray:
    buyruq = ["ffmpeg", "-v", "error", "-i", str(video)]
    if gacha_s:
        buyruq += ["-t", f"{gacha_s:.3f}"]
    buyruq += ["-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    r = subprocess.run(buyruq, capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).copy()


def _df_moslik():
    """DeepFilterNet 0.5.6 eski torchaudio modulini import qiladi; xotirada bo'sh o'rinbosar."""
    if "torchaudio.backend.common" in sys.modules:
        return
    m = types.ModuleType("torchaudio.backend.common")
    m.AudioMetaData = object
    sys.modules.setdefault("torchaudio.backend", types.ModuleType("torchaudio.backend"))
    sys.modules["torchaudio.backend.common"] = m


def tozala(x: np.ndarray):
    """DeepFilterNet3 bilan tozalaydi. Qaytaradi: (tozalangan, sr). x 48 kHz bo'lishi kerak."""
    _df_moslik()
    import torch
    from df.enhance import enhance, init_df
    model, st, _ = init_df(model_base_dir="DeepFilterNet3", log_level="ERROR")
    y = enhance(model, st, torch.from_numpy(x).unsqueeze(0)).squeeze().numpy()
    return y[: len(x)], st.sr()


def rms_db(x: np.ndarray, sr: int, oyna_s: float = K.rms_oyna_s) -> np.ndarray:
    w = int(round(oyna_s * sr))
    n = len(x) // w
    return 20 * np.log10(np.sqrt((x[: n * w].reshape(n, w) ** 2).mean(1)) + 1e-9)


def gap_bolaklari(db: np.ndarray, qadam: float = K.rms_oyna_s, chegara: float = K.gap_chegara_db):
    """Chegaradan baland ketma-ket oynalar -> [(boshi_s, oxiri_s), ...]."""
    s = db > chegara
    bolak, i, n = [], 0, len(s)
    while i < n:
        if s[i]:
            j = i
            while j < n and s[j]:
                j += 1
            bolak.append((round(i * qadam, 4), round(j * qadam, 4)))
            i = j
        else:
            i += 1
    return bolak


NAFAS_CHOQQI_DB = -30.0  # nafas/chertish so'zdan ancha past bo'ladi (taxmin; o'lchangan: nafas ≈ -40 dB, gap ≈ -9 dB)


def birlashtir(bolak, db=None, qadam=K.rms_oyna_s, pauza_min=K.pauza_min_s, nafas_max=NAFAS_MAX_S):
    """Qisqa uzilishlarni birlashtiradi va pauza ichidagi nafasni olib tashlaydi.

    - pauza_min dan qisqa uzilish gap ichidagi tabiiy oraliq: bo'laklar qo'shiladi.
    - Nafas: ikki bo'lak orasidagi, nafas_max dan qisqa VA cho'qqisi NAFAS_CHOQQI_DB dan past bo'lak.
      Cho'qqi sharti qisqa so'zlarni ("u", "va") nafas deb tashlab yubormaslik uchun.
    """
    if not bolak:
        return []
    toza = []
    for k, (a, b) in enumerate(bolak):
        ichida = 0 < k < len(bolak) - 1
        past = True
        if db is not None:
            past = float(np.max(db[int(round(a / qadam)):max(int(round(b / qadam)), int(round(a / qadam)) + 1)])) < NAFAS_CHOQQI_DB
        if ichida and b - a < nafas_max and past:
            continue
        toza.append((a, b))
    natija = [list(toza[0])]
    for a, b in toza[1:]:
        if a - natija[-1][1] < pauza_min:
            natija[-1][1] = b
        else:
            natija.append([a, b])
    return [tuple(x) for x in natija]


def ovoz_tahlili(video, kesh: Path, gacha_s=None, qayta=False) -> dict:
    """Tozalangan ovozni keshga yozadi va gap bo'laklarini qaytaradi."""
    import soundfile as sf
    toza_yol = kesh / "ovoz_tozalangan.wav"
    if toza_yol.exists() and not qayta:
        y, sr = sf.read(toza_yol, dtype="float32")
        asl = audio_oqi(video, sr, gacha_s)
    else:
        sr = 48000
        asl = audio_oqi(video, sr, gacha_s)
        y, sr = tozala(asl)
        sf.write(toza_yol, y, sr, subtype="FLOAT")
    db_asl, db = rms_db(asl, sr), rms_db(y, sr)
    xom = gap_bolaklari(db)
    gaplar = birlashtir(xom, db)
    jim = ~(db > K.gap_chegara_db)
    return {
        "tozalangan_ovoz": str(toza_yol), "sr": sr,
        "shovqin_db": {"asl": round(float(np.median(db_asl[jim])) if jim.any() else 0, 1),
                       "tozalangan": round(float(np.median(db[jim])) if jim.any() else 0, 1)},
        "gap_bolaklari_xom": xom,
        "gap_bolaklari": gaplar,
        "rms_db": db,              # keyingi bosqichlar uchun (JSON ga yozilmaydi)
    }
