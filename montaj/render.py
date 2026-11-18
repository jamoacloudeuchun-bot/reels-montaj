"""B4: render va avtomatik tekshiruv.

CLAUDE.md: "Render faqat tasdiqdan keyin" — `render()` faqat `tasdiq=True` bilan ishlaydi.
Rang: kamera videosi o'z rangida (bt709 -> RGB -> bt709, rang filtri yo'q).
`kadrlar_render_yolida()` — yakuniy render bilan AYNAN bir xil yo'l orqali bir nechta kadr (preview).
"""
import json
import subprocess

import numpy as np
from PIL import Image

from .qoidalar import KADR_BOYI as H, KADR_ENI as W, QOIDALAR
from .vaqt import fps_qiymat

CRF = 17
RANG_SILJISH_MAX = 1.5          # 0–255 shkalada; kamera rangi o'zgarmaganini bildiradi


class TasdiqYoq(PermissionError):
    pass


def _dekoder(video, gacha_s):
    return subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-t", f"{gacha_s:.4f}",
                             "-vf", f"scale={W}:{H}:in_color_matrix=bt709:in_range=tv,format=rgb24",
                             "-f", "rawvideo", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)  # erta yopilganda "Broken pipe" — kutilgan


def _kadr_hisobla(sahna, src_rgb: bytes, t: float) -> Image.Image:
    fr = Image.frombuffer("RGB", (W, H), src_rgb).convert("RGBA")
    q, _ = sahna.qatlam(t)
    return Image.alpha_composite(fr, q).convert("RGB")


def _manba_kadrlari(sahna):
    """Natija kadri n -> manba kadri (tartiblangan)."""
    for a, b in sahna.oraliqlar:
        yield from range(a, b)


def kadrlar_render_yolida(lo, sahna, vaqtlar, papka):
    """Berilgan natija vaqtlaridagi kadrlarni render yo'li orqali chizadi (to'liq render emas)."""
    f = float(fps_qiymat(sahna.fps))
    kerak = {int(round(t * f)): t for t in vaqtlar}
    manba = list(_manba_kadrlari(sahna))
    kerakli_manba = {manba[n]: n for n in kerak}
    oxirgi = max(kerakli_manba)
    dek = _dekoder(lo.video, (oxirgi + 2) / f)
    fs, i, natija = W * H * 3, 0, []
    while i <= oxirgi:
        buf = dek.stdout.read(fs)
        if len(buf) < fs:
            break
        if i in kerakli_manba:
            n = kerakli_manba[i]
            yol = papka / f"{len(natija) + 1}_{kerak[n]:.2f}s.png"
            _kadr_hisobla(sahna, buf, n / f).save(yol)
            natija.append(str(yol))
        i += 1
    dek.stdout.close(); dek.terminate(); dek.wait()
    return natija


def render(lo, sahna, ovoz_wav, chiqish, tasdiq=False) -> str:
    if not tasdiq:
        raise TasdiqYoq("Render faqat foydalanuvchi tasdig'idan keyin (CLAUDE.md). --tasdiq bilan ishga tushiring.")
    f = fps_qiymat(sahna.fps)
    manba = list(_manba_kadrlari(sahna))
    oxirgi = manba[-1]
    keep = set(manba)
    dek = _dekoder(lo.video, (oxirgi + 2) / float(f))
    enk = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(f), "-i", "-", "-i", str(ovoz_wav),
                            "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
                            "-c:v", "libx264", "-preset", "slow", "-crf", str(CRF), "-profile:v", "high",
                            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                            "-color_range", "tv", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                            "-shortest", "-movflags", "+faststart", str(chiqish)], stdin=subprocess.PIPE)
    fs, i, n = W * H * 3, 0, 0
    while i <= oxirgi:
        buf = dek.stdout.read(fs)
        if len(buf) < fs:
            break
        if i in keep:
            enk.stdin.write(_kadr_hisobla(sahna, buf, n / float(f)).tobytes())
            n += 1
        i += 1
    dek.stdout.close(); dek.terminate(); dek.wait()
    enk.stdin.close()
    if enk.wait() != 0:
        raise RuntimeError("kodlash xatosi")
    if n != len(manba):
        raise RuntimeError(f"kadr soni mos emas: {n} != {len(manba)}")
    return str(chiqish)


# ---------------- avtomatik tekshiruv ----------------

def _probe(fayl):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(fayl)],
                       capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def _ebur(fayl):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(fayl), "-af", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True)
    i = tp = None
    for q in r.stderr.splitlines():
        q = q.strip()
        if q.startswith("I:"):
            i = float(q.split()[1])
        elif q.startswith("Peak:"):
            tp = float(q.split()[1])
    return i, tp


def _kadr_yuv(fayl, n, y0, y1):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(fayl), "-vf",
                        f"select=eq(n\\,{n}),scale={W}:{H},crop={W}:{y1 - y0}:0:{y0},format=yuv444p",
                        "-frames:v", "1", "-f", "rawvideo", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(3, y1 - y0, W).astype(float)


def tekshir(lo, sahna, chiqish) -> dict:
    """Format, kadr soni, davomiylik, LUFS/peak, rang (grafika yo'q joyda manba bilan) va A/V uzunligi."""
    d = _probe(chiqish)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    a = next(s for s in d["streams"] if s["codec_type"] == "audio")
    f = float(fps_qiymat(sahna.fps))
    kutilgan = sum(b - a_ for a_, b in sahna.oraliqlar)
    i, tp = _ebur(chiqish)
    # rang: grafika qatlami bo'sh bo'lgan yuqori zona (hook tugagach, pastki gradient boshlanmasdan)
    y1 = int(H * (1 - QOIDALAR.th.qoraytirish_balandlik)) - 10
    hook_oxiri = max((e.oxiri for e in sahna.elementlar if type(e).__name__ == "Hook"), default=0)
    n = min(kutilgan - 1, int((hook_oxiri + 1.0) * f))
    manba_n = list(_manba_kadrlari(sahna))[n]
    m, r = _kadr_yuv(lo.video, manba_n, 0, y1), _kadr_yuv(chiqish, n, 0, y1)
    rang = {c: round(float(np.abs(m[k] - r[k]).mean()), 2) for k, c in enumerate("YUV")}       # siqish shovqini ham kiradi
    siljish = {c: round(float(r[k].mean() - m[k].mean()), 2) for k, c in enumerate("YUV")}   # tizimli rang siljishi
    natija = {
        "fayl": str(chiqish), "kodek": v["codec_name"], "olcham": f"{v['width']}x{v['height']}",
        "fps": v["r_frame_rate"], "kadrlar": int(v.get("nb_frames", 0)), "kutilgan_kadrlar": kutilgan,
        "video_s": round(float(v["duration"]), 3), "ovoz_s": round(float(a["duration"]), 3),
        "lufs": i, "peak_dbfs": tp, "rang_farqi_yuv": rang, "rang_siljishi_yuv": siljish, "rang_tekshiruv_kadri": n,
        "rang_tizimi": [v.get("color_space"), v.get("color_transfer"), v.get("color_primaries")],
    }
    xato = []
    if natija["olcham"] != f"{W}x{H}":
        xato.append("o'lcham 1080x1920 emas")
    if natija["kadrlar"] != kutilgan:
        xato.append(f"kadr soni {natija['kadrlar']} != {kutilgan}")
    if abs(natija["video_s"] - natija["ovoz_s"]) > 0.05:
        xato.append("ovoz va video uzunligi farq qiladi")
    if i is None or abs(i - QOIDALAR.ovoz.yakuniy_lufs) > 1.0:
        xato.append(f"LUFS {i} (kutilgan {QOIDALAR.ovoz.yakuniy_lufs} ±1)")
    if tp is not None and tp > -1.0:
        xato.append(f"peak {tp} dBFS > -1")
    if max(abs(v) for v in siljish.values()) > RANG_SILJISH_MAX:
        xato.append(f"rang siljishi (o'rtacha qiymat farqi) katta: {siljish}")
    if natija["rang_tizimi"] != ["bt709", "bt709", "bt709"]:
        xato.append(f"rang tizimi bt709 emas: {natija['rang_tizimi']}")
    natija["xatolar"] = xato
    natija["holat"] = "OK" if not xato else "XATO"
    return natija
