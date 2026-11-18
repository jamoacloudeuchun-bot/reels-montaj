"""Buyruqlar: python -m montaj <buyruq> <loyiha>

  tekshir   loyiha.json va uslubni tekshiradi
  qabul     videoning texnik tekshiruvi (B2)
  ovoz      ovozni tozalash va gap bo'laklari (B2)
  matn      so'z vaqtlari va matn solishtiruvi (B2)
  kesish    kadr raqamli kesish rejasi (B2)
  tahlil    qabul + ovoz + matn + kesish ketma-ket (B2)
"""
import argparse
import json
import sys

from .loyiha import SozlamaXatosi, loyiha_yukla, uslub_yukla


def _chop(d):
    print(json.dumps(d, ensure_ascii=False, indent=2, default=str))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="montaj")
    ap.add_argument("buyruq", choices=["tekshir", "qabul", "ovoz", "matn", "kesish", "tahlil"])
    ap.add_argument("loyiha")
    ap.add_argument("--qayta", action="store_true", help="keshni e'tiborsiz qoldirib qayta hisoblash")
    a = ap.parse_args(argv)
    try:
        lo = loyiha_yukla(a.loyiha)
        us = uslub_yukla(lo.uslub_nomi)
    except SozlamaXatosi as e:
        print(f"XATO: {e}", file=sys.stderr)
        return 2

    if a.buyruq == "tekshir":
        _chop({"loyiha": lo.nom, "video": lo.video, "video_bor": lo.video.exists(), "uslub": us["nomi"]})
        return 0 if lo.video.exists() else 1

    from . import bosqichlar  # og'ir kutubxonalar faqat kerak bo'lganda yuklanadi
    natija = bosqichlar.ishga_tushir(a.buyruq, lo, qayta=a.qayta)
    _chop(natija)
    return 0


if __name__ == "__main__":
    sys.exit(main())
