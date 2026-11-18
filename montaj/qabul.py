"""1-bosqich: videoning texnik tekshiruvi (ffprobe + ffmpeg)."""
import json
import subprocess

import numpy as np

from .vaqt import fps_qiymat

HDR_TRC = {"smpte2084", "arib-std-b67"}


def _ffprobe(video):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(video)],
        capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def _kadr_vaqtlari(video):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time",
         "-of", "csv=p=0", str(video)], capture_output=True, text=True, check=True)
    t = sorted(float(x) for x in r.stdout.split() if x and x != "N/A")
    return np.array(t)


def _yorqinlik(video, fps_tahlil=10):
    """Har 0.1 s dagi o'rtacha yorqinlik (0–255) — oxiridagi qora/logotip ekranini topish uchun."""
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps={fps_tahlil},scale=32:56,format=gray",
         "-f", "rawvideo", "-"], capture_output=True, check=True)
    kadr = np.frombuffer(r.stdout, np.uint8).reshape(-1, 56 * 32)
    return kadr.mean(1), kadr.std(1), 1 / fps_tahlil


def oxirgi_ekran(yorq, std, qadam, ovoz_rms_db=None, rms_qadam=0.025):
    """Video oxiridagi deyarli bir xil, qorong'i ekranni (masalan ilova logotipi) topadi.

    Shart: kadr qorong'i (o'rtacha < 40) va bir xil (std < 25) bo'lib, video oxirigacha davom etadi.
    Ovoz berilsa, o'sha qismda ovoz ham jim bo'lishi kerak (< -60 dB).
    """
    qora = (yorq < 40) & (std < 25)
    if not qora[-1]:
        return None
    i = len(qora) - 1
    while i > 0 and qora[i - 1]:
        i -= 1
    boshi = i * qadam
    if ovoz_rms_db is not None:
        j = int(boshi / rms_qadam)
        if j < len(ovoz_rms_db) and np.median(ovoz_rms_db[j:]) > -60:
            return None
    return round(boshi, 3)


def qabul(video) -> dict:
    d = _ffprobe(video)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    fps = fps_qiymat(v.get("r_frame_rate", "0/1"))
    t = _kadr_vaqtlari(video)
    dt = np.diff(t) if len(t) > 1 else np.array([0.0])
    nominal = 1 / float(fps) if fps else 0
    vfr = bool(nominal and (np.abs(dt - nominal) > nominal * 0.25).mean() > 0.01)

    burilish = 0
    for sd in v.get("side_data_list", []):
        if "rotation" in sd:
            burilish = int(sd["rotation"])
    burilish = burilish or int(v.get("tags", {}).get("rotate", 0))

    trc = v.get("color_transfer", "")
    eni, boyi = int(v["width"]), int(v["height"])
    if abs(burilish) in (90, 270):
        eni, boyi = boyi, eni
    yorq, std, qadam = _yorqinlik(video)

    natija = {
        "video": str(video),
        "davomiylik_s": round(float(d["format"]["duration"]), 3),
        "kodek": v["codec_name"], "eni": eni, "boyi": boyi, "burilish": burilish,
        "fps": str(fps), "fps_son": round(float(fps), 3), "kadrlar": len(t),
        "vfr": vfr, "pix_fmt": v.get("pix_fmt"),
        "rang": {"space": v.get("color_space"), "transfer": trc, "primaries": v.get("color_primaries")},
        "hdr": trc in HDR_TRC,
        "ovoz": None if not a else {"kodek": a["codec_name"], "sr": int(a["sample_rate"]),
                                    "kanal": int(a.get("channels", 0))},
        "oxirgi_qora_ekran_s": oxirgi_ekran(yorq, std, qadam),
    }
    ogoh = []
    if natija["hdr"]:
        ogoh.append("HDR video: SDR ga o'tkazishda rang siljishi mumkin — asl/yangi kadrni taqqoslab tasdiqlash kerak")
    if vfr:
        ogoh.append("O'zgaruvchan kadr tezligi (VFR): kesishdan oldin doimiy fps ga o'tkazish kerak")
    if (eni, boyi) != (1080, 1920):
        ogoh.append(f"O'lcham {eni}x{boyi}: 1080x1920 ga moslash kerak")
    if not a:
        ogoh.append("Ovoz yo'lagi yo'q")
    if natija["oxirgi_qora_ekran_s"] is not None:
        ogoh.append(f"Oxirida {natija['oxirgi_qora_ekran_s']} s dan qorong'i bir xil ekran bor (ilova logotipi bo'lishi mumkin)")
    natija["ogohlantirishlar"] = ogoh
    return natija
