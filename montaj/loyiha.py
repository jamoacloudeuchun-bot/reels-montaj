"""Loyiha va uslub sozlamalarini yuklash.

Loyiha: `loyihalar/<nom>/loyiha.json`
    {
      "nom": "…",
      "video": "/yo'l/asl_video.mov",       # repodan tashqarida, git'ga tushmaydi
      "matn": "Foydalanuvchi tasdiqlagan matn",
      "hook": "HOOK MATNI" | null,
      "uslub": "asosiy",                    # uslublar/<uslub>/uslub.json
      "til": "uz",
      "soz_vaqtlari": [{"soz": "Biz", "boshi": 7.58}],  # ixtiyoriy: quloq bilan tasdiqlangan vaqtlar
      "musiqa": {"fayl": "/yo'l/trek.mp3", "boshi_s": null},  # ixtiyoriy, foydalanuvchi fayli
      "asosiy_moment_s": null,             # ixtiyoriy: musiqa drop'i to'g'rilanadigan natija vaqti
      "sfx": [{"fayl": "/yo'l/pop.wav", "t": 2.4}]          # ixtiyoriy: faqat grafika paydo bo'lganda
    }
Natija va kesh fayllari `loyihalar/<nom>/kesh/` va `.../natija/` ga yoziladi (git'dan tashqarida).
"""
import json
from dataclasses import dataclass
from pathlib import Path

ILDIZ = Path(__file__).resolve().parent.parent
USLUBLAR = ILDIZ / "uslublar"
LOYIHALAR = ILDIZ / "loyihalar"

MAJBURIY = ("nom", "video", "matn")


class SozlamaXatosi(ValueError):
    pass


@dataclass
class Loyiha:
    nom: str
    video: Path
    matn: str
    hook: str | None
    uslub_nomi: str
    til: str
    papka: Path
    soz_vaqtlari: list | None = None
    musiqa: dict | None = None
    asosiy_moment_s: float | None = None
    sfx: list | None = None
    grafikalar: list | None = None

    @property
    def kesh(self) -> Path:
        p = self.papka / "kesh"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def natija(self) -> Path:
        p = self.papka / "natija"
        p.mkdir(parents=True, exist_ok=True)
        return p


def loyiha_yukla(yol) -> Loyiha:
    yol = Path(yol)
    if yol.is_dir():
        yol = yol / "loyiha.json"
    if not yol.exists() and not yol.is_absolute():
        yol = LOYIHALAR / yol / "loyiha.json"
    if not yol.exists():
        raise SozlamaXatosi(f"loyiha.json topilmadi: {yol}")
    d = json.loads(yol.read_text(encoding="utf-8"))
    yoq = [k for k in MAJBURIY if not d.get(k)]
    if yoq:
        raise SozlamaXatosi(f"loyiha.json da majburiy maydon yo'q: {', '.join(yoq)}")
    return Loyiha(
        nom=d["nom"],
        video=Path(d["video"]),
        matn=d["matn"].strip(),
        hook=(d.get("hook") or None),
        uslub_nomi=d.get("uslub", "asosiy"),
        til=d.get("til", "uz"),
        papka=yol.parent,
        soz_vaqtlari=d.get("soz_vaqtlari"),
        musiqa=d.get("musiqa"),
        asosiy_moment_s=d.get("asosiy_moment_s"),
        sfx=d.get("sfx"),
        grafikalar=d.get("grafikalar"),
    )


def uslub_yukla(nom: str = "asosiy") -> dict:
    """Uslub paketini nomi bo'yicha yuklaydi. Yadro hech qaysi paketni nomini bilmaydi."""
    yol = USLUBLAR / nom / "uslub.json"
    if not yol.exists():
        mavjud = sorted(p.name for p in USLUBLAR.iterdir() if (p / "uslub.json").exists())
        raise SozlamaXatosi(f"uslub topilmadi: {nom}. Mavjud: {', '.join(mavjud)}")
    d = json.loads(yol.read_text(encoding="utf-8"))
    d["_papka"] = str(yol.parent)
    return d


def shrift_yoli(nisbiy: str) -> Path:
    """Uslubdagi shrift yo'li: repo ichidagi nisbiy yo'l yoki tizimdagi mutlaq yo'l."""
    p = Path(nisbiy)
    return p if p.is_absolute() else ILDIZ / p
