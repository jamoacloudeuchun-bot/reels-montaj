"""B4: ovoz miksi.

CLAUDE.md:
- Nutq: DeepFilterNet bilan tozalangan ovoz, video bilan bir xil kadr chegaralarida kesiladi.
- Musiqa (ixtiyoriy, foydalanuvchi fayli): ≈ -21 LUFS (-12 dB), nutq ostida pasayadi (ducking).
  Boshlanish soniyasi berilmasa — trekdagi zarba (drop) asosiy momentga to'g'rilanadi.
- SFX (ixtiyoriy, haqiqiy yozuvlar): faqat grafika paydo bo'lganda; nutq ustiga tushsa -5 dB.
- Yakuniy -14 LUFS (ikki bosqichli loudnorm), true peak -1.5 dBFS.
"""
import json
import subprocess

import numpy as np

from .qoidalar import QOIDALAR
from .vaqt import fps_qiymat

O = QOIDALAR.ovoz
SR = 48000
ULANISH_FADE_S = 0.005          # kesim joyida chertish bo'lmasligi uchun
TRUE_PEAK = -1.5


def _oqi(fayl, sr=SR) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(fayl), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).copy()


def nutqni_kes(nutq: np.ndarray, sr: int, oraliqlar, fps) -> np.ndarray:
    """Kadr oraliqlari [boshi, oxiri) bo'yicha namuna-aniq kesish, har ulanishda 5 ms fade."""
    f = fps_qiymat(fps)
    bolak = []
    n_fade = int(ULANISH_FADE_S * sr)
    for a, b in oraliqlar:
        i0, i1 = round(a * sr / f), round(b * sr / f)
        x = np.zeros(i1 - i0, np.float32)
        mavjud = nutq[i0:min(i1, len(nutq))]
        x[:len(mavjud)] = mavjud
        if len(x) > 2 * n_fade:
            x[:n_fade] *= np.linspace(0, 1, n_fade)
            x[-n_fade:] *= np.linspace(1, 0, n_fade)
        bolak.append(x)
    return np.concatenate(bolak)


def drop_vaqti(musiqa: np.ndarray, sr: int, oyna_s=0.5) -> float:
    """Trekdagi eng keskin energiya ko'tarilishi (drop) vaqti — oddiy, kutubxonasiz baho."""
    w = int(oyna_s * sr)
    n = len(musiqa) // w
    if n < 3:
        return 0.0
    e = 20 * np.log10(np.sqrt((musiqa[:n * w].reshape(n, w) ** 2).mean(1)) + 1e-9)
    return float((int(np.argmax(np.diff(e))) + 1) * oyna_s)


def lufs(x: np.ndarray, sr: int) -> float:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-",
                        "-af", "ebur128", "-f", "null", "-"], input=x.astype(np.float32).tobytes(),
                       capture_output=True)
    for q in r.stderr.decode().splitlines()[::-1]:
        if q.strip().startswith("I:"):
            return float(q.split()[1])
    return float("nan")


def _gain(x, db):
    return x * (10 ** (db / 20))


def musiqa_qosh(nutq, sr, musiqa_fayl, boshi_s=None, asosiy_moment_s=0.0, nutq_maskasi=None):
    """Musiqani -21 LUFS ga keltirib, nutq ostida ducking bilan qo'shadi. Qaytaradi: (aralashma, info)."""
    m = _oqi(musiqa_fayl, sr)
    if boshi_s is None:
        d = drop_vaqti(m, sr)
        boshi_s = max(0.0, d - asosiy_moment_s)
        manba = "drop asosiy momentga to'g'rilandi (taxmin)"
    else:
        manba = "foydalanuvchi"
    m = m[int(boshi_s * sr):int(boshi_s * sr) + len(nutq)]
    m = np.pad(m, (0, max(0, len(nutq) - len(m))))
    m = _gain(m, O.musiqa_lufs - lufs(m, sr))
    if nutq_maskasi is not None:                           # ducking: nutq paytida -6 dB, yumshoq o'tish
        k = int(0.15 * sr)
        mask = np.convolve(nutq_maskasi.astype(float), np.ones(k) / k, mode="same")
        m = m * (10 ** (-6 * np.clip(mask, 0, 1) / 20))
    n = len(nutq)
    fade = int(0.5 * sr)
    m[-fade:] *= np.linspace(1, 0, min(fade, n))
    return nutq + m, {"musiqa_boshi_s": round(boshi_s, 3), "manba": manba}


def sfx_qosh(aralash, sr, hodisalar, grafika_vaqtlari, nutq_maskasi=None):
    """hodisalar: [{"fayl": ..., "t": natija_s}] — faqat grafika paydo bo'ladigan vaqtga (±0.1 s)."""
    for h in hodisalar or []:
        if not any(abs(h["t"] - g) <= 0.1 for g in grafika_vaqtlari):
            raise ValueError(f"SFX {h['t']} s da grafika yo'q — CLAUDE.md: SFX faqat grafikaga")
        s = _oqi(h["fayl"], sr)
        i = int(h["t"] * sr)
        s = s[:max(0, len(aralash) - i)]
        if nutq_maskasi is not None and nutq_maskasi[i:i + len(s)].any():
            s = _gain(s, O.sfx_gap_ustida_db)
        aralash[i:i + len(s)] += s
    return aralash


def normallashtir(x: np.ndarray, sr: int, chiqish) -> dict:
    """Ikki bosqichli loudnorm: -14 LUFS, TP -1.5 dBFS. 16-bit WAV yozadi."""
    sozlama = f"loudnorm=I={O.yakuniy_lufs}:TP={TRUE_PEAK}:LRA=11"
    raw = x.astype(np.float32).tobytes()
    kirish = ["-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-"]
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *kirish, "-af", sozlama + ":print_format=json",
                        "-f", "null", "-"], input=raw, capture_output=True)
    t = r.stderr.decode()
    o = json.loads(t[t.rindex("{"):t.rindex("}") + 1])
    ikkinchi = (f"{sozlama}:measured_I={o['input_i']}:measured_TP={o['input_tp']}:measured_LRA={o['input_lra']}"
                f":measured_thresh={o['input_thresh']}:offset={o['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *kirish, "-af", ikkinchi + f",aresample={SR}",
                    "-c:a", "pcm_s16le", str(chiqish)], input=raw, check=True)
    return {"kirish_lufs": float(o["input_i"]), "kirish_tp": float(o["input_tp"])}


def ovoz_tayyorla(lo, kesish_n, sahna, tozalangan_wav) -> dict:
    import soundfile as sf
    nutq, sr = sf.read(tozalangan_wav, dtype="float32")
    orl = [tuple(x) for x in kesish_n["saqlanadigan_kadrlar"]]
    x = nutqni_kes(nutq, sr, orl, kesish_n["fps"])
    kutilgan = round(kesish_n["natija_kadr"] * sr / float(fps_qiymat(kesish_n["fps"])))
    assert abs(len(x) - kutilgan) <= len(orl), "ovoz uzunligi video bilan mos emas"
    maska = np.abs(x) > 10 ** (QOIDALAR.kesish.gap_chegara_db / 20)
    info = {"musiqa": None, "sfx": 0}
    if lo.musiqa:
        moment = lo.asosiy_moment_s if lo.asosiy_moment_s is not None else next(
            (e.boshi for e in sahna.elementlar if type(e).__name__ == "Subtitr"), 0.0)
        x, info["musiqa"] = musiqa_qosh(x, sr, lo.musiqa.get("fayl"), lo.musiqa.get("boshi_s"), moment, maska)
    if lo.sfx:
        gv = [e.boshi for e in sahna.elementlar if type(e).__name__ in ("Kartochka", "Royxat")]
        x = sfx_qosh(x, sr, lo.sfx, gv, maska)
        info["sfx"] = len(lo.sfx)
    yol = lo.kesh / "ovoz_yakuniy.wav"
    info.update(normallashtir(x, sr, yol))
    info["fayl"] = str(yol)
    info["davomiylik_s"] = round(len(x) / sr, 4)
    return info
