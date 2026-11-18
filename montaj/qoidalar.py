"""CLAUDE.md dagi montaj qoidalari — yadroning yagona raqamli manbai.

Bu yerdagi qiymatlar CLAUDE.md ni takrorlaydi va undan tashqariga chiqmaydi.
`testlar/test_qoidalar.py` har bir qiymat CLAUDE.md matnida borligini tekshiradi,
shuning uchun CLAUDE.md o'zgarsa, testlar buni darhol ko'rsatadi.
Mavzu, matn, rang (oqdan boshqa) yoki brend bu faylda bo'lmaydi.
"""
from dataclasses import dataclass, field

KADR_ENI = 1080
KADR_BOYI = 1920


@dataclass(frozen=True)
class SafeZona:
    x: tuple = (150, 930)
    y: tuple = (230, 1595)
    markaz_matn_eni_max: int = 780      # "≤ 720–780 px"
    yon_kartochka_min_x: int = 80


@dataclass(frozen=True)
class TalkingHead:
    hook_y: int = 420
    koz_y: int = 810
    subtitr_y: int = 1260
    kattalashtirish_foiz: tuple = (120, 130)
    qoraytirish_kuch: float = 0.55
    qoraytirish_balandlik: float = 0.70


@dataclass(frozen=True)
class Matn:
    rang: str = "#FFFFFF"
    tracking: tuple = (0, 20)
    izoh_px: int = 44
    izoh_opacity: float = 1.0
    sarlavha_soya: bool = False
    logotip_plitka_px: tuple = (140, 200)


@dataclass(frozen=True)
class Kesish:
    bosh_zaxira_s: float = 0.05
    oxir_zaxira_s: float = 0.08
    pauza_min_s: float = 0.25
    pauza_qoldiq_s: float = 0.12
    gap_chegara_db: float = -42.0
    rms_oyna_s: float = 0.025
    whisper_oldinda_s: tuple = (0.4, 0.5)


@dataclass(frozen=True)
class Ovoz:
    musiqa_db: float = -12.0
    musiqa_lufs: float = -21.0
    yakuniy_lufs: float = -14.0
    sfx_gap_ustida_db: float = -5.0
    sfx_turlari: tuple = ("pop", "whoosh", "hit")


@dataclass(frozen=True)
class Animatsiya:
    pop_foiz: tuple = (80, 106, 100)
    pop_s: tuple = (0.2, 0.34)
    matn_kotarilish_px: int = 36
    matn_fade_s: float = 0.2
    chiqish_fade_s: tuple = (0.2, 0.3)
    zoom_foiz: tuple = (100, 109, 111)
    zoom_kirish_s: float = 0.3
    zoom_chiqish_s: float = 0.35


@dataclass(frozen=True)
class Qoidalar:
    safe: SafeZona = field(default_factory=SafeZona)
    th: TalkingHead = field(default_factory=TalkingHead)
    matn: Matn = field(default_factory=Matn)
    kesish: Kesish = field(default_factory=Kesish)
    ovoz: Ovoz = field(default_factory=Ovoz)
    anim: Animatsiya = field(default_factory=Animatsiya)
    render_tasdiqsiz: bool = False      # "Render faqat tasdiqdan keyin"
    rang_ozgartirish: bool = False      # "Kamera videosi o'z rangida qoladi"


QOIDALAR = Qoidalar()
