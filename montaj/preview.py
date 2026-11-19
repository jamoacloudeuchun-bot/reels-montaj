"""Preview kadrlar: manba kadri + sahna qatlami (rang o'zgarmaydi) va safe zona ramkali varaq."""
import io
import json
import subprocess

from PIL import Image

from .qoidalar import QOIDALAR
from .sahna import safe_tekshir, sahna_qur
from .vaqt import kadr_vaqti

S, TH = QOIDALAR.safe, QOIDALAR.th


def manba_kadr(video, kadr, fps) -> Image.Image:
    t = kadr_vaqti(kadr, fps)
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.6f}", "-i", str(video), "-frames:v", "1",
                        "-vf", "scale=in_color_matrix=bt709:in_range=tv,format=rgb24",
                        "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, check=True)
    return Image.open(io.BytesIO(r.stdout)).convert("RGBA")


def vaqtlarni_tanla(sahna, n=4):
    """Hook (pop tugagach), grafika komponentlari (animatsiya tugagan payt) va subtitrlar o'rtasi.

    Grafika bo'lsa, ular birinchi navbatda ko'rsatiladi; joy qolsa — subtitrlar.
    """
    hook, graf, sub = [], [], []
    for e in sahna.elementlar:
        nom = type(e).__name__
        if nom == "Hook":
            hook.append(min(e.boshi + 0.8, (e.boshi + e.oxiri) / 2))
        elif nom == "Subtitr":
            sub.append((e.boshi + e.oxiri) / 2)
        elif nom != "PastkiGradient":
            graf.append(min(e.boshi + getattr(e, "toliq_korinish_s", 1.4), (e.boshi + e.oxiri) / 2 + 0.3, e.oxiri - 0.3))
    t = (hook + graf + sub)[:n]
    return sorted(round(x, 3) for x in t)


def safe_ramka(png_yol, chiqish):
    """CLAUDE.md: safe zona ramkasini ffmpeg drawbox bilan chizib tekshirish."""
    vf = (f"drawbox=x={S.x[0]}:y={S.y[0]}:w={S.x[1] - S.x[0]}:h={S.y[1] - S.y[0]}:color=red@0.9:t=4,"
          f"drawbox=x=0:y={TH.koz_y - 2}:w=1080:h=4:color=yellow@0.8:t=fill,"
          f"drawbox=x=0:y={TH.hook_y - 2}:w=1080:h=4:color=cyan@0.8:t=fill,"
          f"drawbox=x=0:y={TH.subtitr_y - 2}:w=1080:h=4:color=cyan@0.8:t=fill")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(png_yol), "-vf", vf, str(chiqish)], check=True)


def preview(lo, uslub, matn_n, kesish_n, vaqtlar=None) -> dict:
    sahna = sahna_qur(lo, uslub, matn_n, kesish_n)
    papka = lo.natija / "preview"
    papka.mkdir(parents=True, exist_ok=True)
    for eski in papka.glob("*"):
        eski.unlink()
    vaqtlar = vaqtlar or vaqtlarni_tanla(sahna)
    fayllar, ramkali = [], []
    for i, t in enumerate(vaqtlar, 1):
        k = sahna.manba_kadri(t)
        q, _ = sahna.qatlam(t)
        img = Image.alpha_composite(manba_kadr(lo.video, k, sahna.fps), q).convert("RGB")
        yol = papka / f"{i}_{t:.2f}s.png"
        img.save(yol)
        r = papka / f"safe_{i}.png"
        safe_ramka(yol, r)
        fayllar.append(str(yol)); ramkali.append(r)
    varaq = papka / "safe_zona_tekshiruv.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *sum((["-i", str(r)] for r in ramkali), []),
                    "-filter_complex", f"{''.join(f'[{i}]' for i in range(len(ramkali)))}hstack={len(ramkali)},scale=2160:-1",
                    str(varaq)], check=True)
    for r in ramkali:
        r.unlink()
    xato = safe_tekshir(sahna)
    jad = [{"element": type(e).__name__, "boshi": e.boshi, "oxiri": e.oxiri,
            "matn": getattr(e, "matn", None)} for e in sahna.elementlar]
    (lo.kesh / "sahna.json").write_text(json.dumps(jad, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"kadrlar": fayllar, "safe_varaq": str(varaq), "safe_buzilishlar": xato, "jadval": jad,
            "davomiylik_s": round(sahna.davomiylik, 3)}
