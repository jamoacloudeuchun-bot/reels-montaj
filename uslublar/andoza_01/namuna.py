"""Andoza_01 uslubini sinash uchun SINTETIK namuna loyihasi (haqiqiy video emas).

python uslublar/andoza_01/namuna.py [papka] [davomiylik_s]

Yaratadi: sintetik video (ffmpeg gradients + ton), loyiha.json, kesh/matn.json (teng taqsimlangan
so'z vaqtlari), kesh/kesish.json (butun video) va kesh/ovoz_tozalangan.wav. Whisper/DeepFilterNet
ishlatilmaydi. Barcha matnlar — neytral namuna matnlar (andozadan ko'chirilmagan).
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ILDIZ = Path(__file__).resolve().parents[2]
SR = 48000

MATN = ("Bu sintetik sinov videosi. Uslub komponentlari tekshirilmoqda: raqam, ro‘yxat, kartochka va sana. "
        "Barcha matnlar namuna uchun yozilgan.")


def grafikalar(dav):
    k = dav / 16
    return [
        {"tur": "RaqamSahna", "boshi_s": 0.6 * k, "oxiri_s": 3.8 * k, "yorliq": "1-komponent",
         "sarlavha": "RAQAM VA SHKALA", "raqam": "4–7", "birlik": "qadam", "shkala": [1, 10], "qiymat": [4, 7]},
        {"tur": "LowerThird", "boshi_s": 4.3 * k, "oxiri_s": 6.6 * k, "yorliq": "2-komponent",
         "matn": "Kartochka", "ikonka": "odam"},
        {"tur": "ChecklistSahna", "boshi_s": 7.0 * k, "oxiri_s": 10.8 * k, "yorliq": "3-komponent",
         "sarlavha": "RO‘YXAT", "bandlar": ["Birinchi band", "Ikkinchi band", "Uchinchi band"], "belgilangan": [0, 1]},
        {"tur": "SanaSahna", "boshi_s": 11.2 * k, "oxiri_s": 13.8 * k, "yorliq": "4-komponent",
         "sarlavha": "SANA KARTOCHKALARI",
         "sanalar": [{"oy": "yanvar", "kun": "12", "izoh": "boshlanish"}, {"oy": "fevral", "kun": "28", "izoh": "tugash"}]},
        {"tur": "DoiraSahna", "boshi_s": 14.0 * k, "oxiri_s": 15.8 * k, "yorliq": "5-komponent", "raqam": "5",
         "izoh": "doira"},
    ]


def yarat(papka: Path, dav: float = 16.0, fps: int = 30) -> Path:
    papka = Path(papka)
    kesh = papka / "kesh"
    kesh.mkdir(parents=True, exist_ok=True)
    video = kesh / "sintetik.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    f"gradients=s=1080x1920:r={fps}:d={dav}:c0=0x3a4a5a:c1=0x8a7a60:c2=0x2a3a2a:speed=0.02",
                    "-f", "lavfi", "-i", f"sine=f=220:d={dav}:sample_rate={SR}",
                    "-vf", "drawtext=fontfile=/usr/share/fonts/opentype/inter/Inter-Bold.otf:text='SINTETIK TEST':"
                           "fontsize=64:fontcolor=white@0.35:x=(w-tw)/2:y=880",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709",
                    "-color_trc", "bt709", "-c:a", "aac", "-shortest", str(video)], check=True)
    loyiha = {"nom": papka.name, "video": str(video), "matn": MATN, "hook": None, "uslub": "andoza_01", "til": "uz",
              "grafikalar": grafikalar(dav)}
    (papka / "loyiha.json").write_text(json.dumps(loyiha, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sozlar = MATN.split()
    qadam = (dav - 0.6) / len(sozlar)
    (kesh / "matn.json").write_text(json.dumps({"sozlar": [
        {"soz": s, "boshi": round(0.3 + i * qadam, 3), "oxiri": round(0.3 + (i + 1) * qadam, 3), "manba": "sintetik"}
        for i, s in enumerate(sozlar)]}, ensure_ascii=False), encoding="utf-8")
    n = int(dav * fps)
    (kesh / "kesish.json").write_text(json.dumps({"fps": f"{fps}/1", "saqlanadigan_kadrlar": [[0, n]],
                                                  "natija_kadr": n}), encoding="utf-8")
    import soundfile as sf
    t = np.arange(int(dav * SR)) / SR
    x = (0.3 * np.sin(2 * np.pi * 220 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t))).astype(np.float32)
    sf.write(kesh / "ovoz_tozalangan.wav", x, SR, subtype="FLOAT")
    return papka


if __name__ == "__main__":
    p = Path(sys.argv[1]) if len(sys.argv) > 1 else ILDIZ / "loyihalar" / "namuna_andoza_01"
    print(yarat(p, float(sys.argv[2]) if len(sys.argv) > 2 else 16.0))
