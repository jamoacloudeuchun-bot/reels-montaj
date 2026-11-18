"""Bosqichlarni ketma-ket bajarish va natijalarni loyiha keshiga yozish."""
import json

from .kesish import kesish_rejasi
from .matn import matn_bosqichi
from .ovoz import ovoz_tahlili
from .qabul import qabul


def _yoz(lo, nom, d):
    toza = {k: v for k, v in d.items() if k != "rms_db"}
    (lo.kesh / f"{nom}.json").write_text(json.dumps(toza, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return toza


def _qabul(lo, qayta):
    yol = lo.kesh / "qabul.json"
    if yol.exists() and not qayta:
        return json.loads(yol.read_text(encoding="utf-8"))
    return _yoz(lo, "qabul", qabul(lo.video))


def _ovoz(lo, q, qayta):
    d = ovoz_tahlili(lo.video, lo.kesh, gacha_s=q.get("oxirgi_qora_ekran_s"), qayta=qayta)
    d["gacha_s"] = q.get("oxirgi_qora_ekran_s")
    _yoz(lo, "ovoz", d)
    return d


def ishga_tushir(buyruq, lo, qayta=False) -> dict:
    if buyruq == "preview":
        return _preview(lo, qayta)
    if not lo.video.exists():
        raise FileNotFoundError(f"video topilmadi: {lo.video}")
    q = _qabul(lo, qayta and buyruq in ("qabul", "tahlil"))
    if buyruq == "qabul":
        return q
    ov = _ovoz(lo, q, qayta and buyruq in ("ovoz", "tahlil"))
    if buyruq == "ovoz":
        return {k: v for k, v in ov.items() if k != "rms_db"}
    natija = {"qabul": q, "ovoz": {k: v for k, v in ov.items() if k != "rms_db"}}
    if buyruq in ("matn", "tahlil"):
        natija["matn"] = _yoz(lo, "matn", matn_bosqichi(lo, ov, qayta=qayta and buyruq in ("matn", "tahlil")))
        if buyruq == "matn":
            return natija["matn"]
    reja = kesish_rejasi(ov["gap_bolaklari"], q["fps"], q["kadrlar"], chegara_s=q.get("oxirgi_qora_ekran_s"))
    natija["kesish"] = _yoz(lo, "kesish", reja)
    if buyruq == "kesish":
        return reja
    (lo.natija / "tahlil_hisoboti.md").write_text(hisobot(lo, natija), encoding="utf-8")
    return natija


def hisobot(lo, n) -> str:
    q, o, k = n["qabul"], n["ovoz"], n["kesish"]
    m = n.get("matn", {})
    s = [f"# Tahlil hisoboti — {lo.nom}", "",
         "## Qabul [o'lchandi]",
         f"- {q['kodek']}, {q['eni']}×{q['boyi']}, {q['fps_son']} fps, {q['kadrlar']} kadr, {q['davomiylik_s']} s",
         f"- Rang: {q['rang']}, HDR: {'ha' if q['hdr'] else 'yo‘q'}, VFR: {'ha' if q['vfr'] else 'yo‘q'}"]
    s += [f"- ⚠️ {g}" for g in q.get("ogohlantirishlar", [])]
    s += ["", "## Ovoz [o'lchandi]",
          f"- Shovqin: {o['shovqin_db']['asl']} dB → {o['shovqin_db']['tozalangan']} dB (DeepFilterNet)",
          f"- Gap bo'laklari: {o['gap_bolaklari']}"]
    if m:
        s += ["", "## Matn", f"- Whisper bilan mos so'zlar ulushi: {int(m['mos_ulush'] * 100)}%",
              f"- Eshitilgan (xom, Whisper): {m['eshitilgan_xom']}", "", "### Farqlar (tasdiqlash kerak)"]
        s += [f"- {f['boshi']}–{f['oxiri']} s: matnda «{f['matnda']}» · eshitildi «{f['eshitildi']}» (p≥{f['p_min']})"
              for f in m["farqlar"]] or ["- yo'q"]
        s += ["", "### Noaniq so'zlar (p < 0.5)"]
        s += [f"- {w['boshi']}–{w['oxiri']} s: «{w['soz']}» p={w['p']}" for w in m["noaniq"]] or ["- yo'q"]
    s += ["", "## Kesish rejasi",
          f"- Saqlanadigan kadrlar [boshi, oxiri): {k['saqlanadigan_kadrlar']}",
          f"- Natija: {k['natija_kadr']} kadr = {k['natija_s']} s"]
    s += [f"- Pauza {p['oraliq_s']} s: {p['asl_s']} → {p['yangi_s']} s (kadrlar {p['olib_tashlanadi_kadr']} olib tashlanadi)"
          for p in k["pauzalar"]]
    if k.get("olib_tashlangan_oxir_s") is not None:
        s.append(f"- {k['olib_tashlangan_oxir_s']} s dan keyingi oxirgi ekran olib tashlanadi")
    return "\n".join(s) + "\n"


def _preview(lo, qayta):
    from .loyiha import uslub_yukla
    from .preview import preview
    m, k = lo.kesh / "matn.json", lo.kesh / "kesish.json"
    if qayta or not (m.exists() and k.exists()):
        ishga_tushir("tahlil", lo, qayta=qayta)
    return preview(lo, uslub_yukla(lo.uslub_nomi), json.loads(m.read_text(encoding="utf-8")),
                   json.loads(k.read_text(encoding="utf-8")))
