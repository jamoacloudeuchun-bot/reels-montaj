"""Har pozada yuz detallarining joyini avtomatik topadi: og'iz (o'chirish va almashtirish uchun)
va ko'zlar (qirpish uchun). Natija: yuz.json + korik/yuz_topildi.png (tekshirish uchun).

Usul (tekis rangli multfilm uchun):
- teri maskasi (teri rangiga yaqin piksellar), yuz = eng yuqoridagi katta teri komponenti;
- og'iz = yuzning pastki qismidagi, teri bilan o'ralgan to'q chiziq komponenti;
- ko'z = yuzning o'rta qismidagi to'ldirilgan to'q dog' (qorachiq) + unga tegib turgan oq (ko'z oqi).
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "quyosh_panel"))
from stiker_kes import _kengay, komponentlar  # noqa: E402

TERI = np.array([253, 197, 146])


def topish(f):
    a = np.asarray(Image.open(f).convert("RGBA")).astype(int)
    rgb, al = a[..., :3], a[..., 3] > 128
    teri = (np.abs(rgb - TERI).sum(2) < 75) & al
    belgi, komp = komponentlar(teri, min_maydon=400)
    # peshona: eng yuqoridagi katta teri komponenti; yuz = peshona ostidagi teri bo'laklari (ko'zoynak
    # terini bo'lib yuboradi: yonoqlar, burun, iyak alohida komponent bo'ladi)
    pesh = min(komp, key=lambda k: (k[0] + k[1]) / 2 if k[5] > 2000 else 1e9)
    pw = pesh[3] - pesh[2]
    yuz_k = [k for k in komp if pesh[2] - 0.15 * pw <= (k[2] + k[3]) / 2 <= pesh[3] + 0.15 * pw
             and pesh[0] <= (k[0] + k[1]) / 2 <= pesh[0] + 1.05 * pw and (k[3] - k[2]) < 1.3 * pw]
    y0 = min(k[0] for k in yuz_k); y1 = max(k[1] for k in yuz_k)
    x0 = min(k[2] for k in yuz_k); x1 = max(k[3] for k in yuz_k)
    yuz_maska = np.isin(belgi, [k[4] for k in yuz_k])
    fh, fw = y1 - y0, x1 - x0
    tq = (rgb.sum(2) < 230) & al
    # yuz ichidagi to'q piksellar: yuz komponentining "teshiklari" (bbox ichida, atrofi teri)
    ichki = np.zeros_like(tq)
    yuz_m = _kengay(yuz_maska, 4)
    ichki[y0:y1, x0:x1] = tq[y0:y1, x0:x1] & yuz_m[y0:y1, x0:x1]
    bl, kk = komponentlar(ichki, min_maydon=8)
    cx_yuz = (x0 + x1) / 2
    # og'iz: yuzning 60–95% balandligida, gorizontal cho'zilgan, markazga eng yaqin
    og = [k for k in kk if y0 + 0.58 * fh < (k[0] + k[1]) / 2 < y0 + 0.97 * fh
          and (k[3] - k[2]) > 1.5 * (k[1] - k[0]) and (k[3] - k[2]) > 0.12 * fw]
    ogiz = min(og, key=lambda k: abs((k[2] + k[3]) / 2 - cx_yuz)) if og else None
    # ko'zlar: yuzning o'rta qismidagi ikkita katta oq dog' (ko'z oqi); qorachiq uning ichida
    oq = (rgb.min(2) > 215) & al
    oqm = np.zeros_like(oq)
    oqm[y0:y1, x0:x1] = oq[y0:y1, x0:x1]
    bo, ko = komponentlar(oqm, min_maydon=25)
    ko = [k for k in ko if y0 + 0.25 * fh < (k[0] + k[1]) / 2 < y0 + 0.7 * fh]
    ko = sorted(sorted(ko, key=lambda k: -k[5])[:2], key=lambda k: k[2])
    koz = []
    for k in ko:
        # ko'z oqi + ichidagi qorachiq: oq bbox atrofidagi to'q piksellar bilan kengaytirilgan chegara
        koz.append([int(k[2]) - 1, int(k[0]) - 1, int(k[3]) + 1, int(k[1]) + 1])
    return {
        "yuz": [int(x0), int(y0), int(x1), int(y1)],
        "ogiz": None if ogiz is None else [int(ogiz[2]), int(ogiz[0]), int(ogiz[3]), int(ogiz[1])],
        "kozlar": koz,
    }


if __name__ == "__main__":
    papka = Path(sys.argv[1])
    natija = {}
    rasmlar = []
    for f in sorted(papka.glob("*.png")):
        r = topish(f)
        natija[f.stem] = r
        im = Image.open(f).convert("RGBA")
        d = ImageDraw.Draw(im)
        d.rectangle(r["yuz"], outline=(0, 200, 0, 255))
        if r["ogiz"]:
            d.rectangle(r["ogiz"], outline=(255, 0, 0, 255), width=2)
        for k in r["kozlar"]:
            d.rectangle(k, outline=(0, 120, 255, 255), width=2)
        x0, y0, x1, y1 = r["yuz"]
        rasmlar.append(im.crop((x0 - 10, y0 - 10, x1 + 10, y1 + 10)).resize(((x1 - x0 + 20) * 2, (y1 - y0 + 20) * 2)))
        print(f.stem, r)
    json.dump(natija, open("yuz.json", "w"), indent=1)
    W = sum(r.width for r in rasmlar) + 10 * len(rasmlar)
    v = Image.new("RGBA", (W, max(r.height for r in rasmlar)), (30, 40, 90, 255))
    x = 0
    for r in rasmlar:
        v.alpha_composite(r, (x, 0)); x += r.width + 10
    v.convert("RGB").save("korik/yuz_topildi.png")
