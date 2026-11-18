"""B4: ovoz miksi, render darvozasi (tasdiq), render va avtomatik tekshiruv — sintetik video bilan."""
import subprocess
from types import SimpleNamespace

import numpy as np
import pytest
import soundfile as sf

from montaj.grafika.elementlar import PastkiGradient, Subtitr
from montaj.loyiha import uslub_yukla
from montaj.ovoz_miks import drop_vaqti, lufs, normallashtir, nutqni_kes, sfx_qosh
from montaj.render import TasdiqYoq, render, tekshir
from montaj.sahna import Sahna

SR = 48000
US = uslub_yukla("asosiy")


def test_nutq_kadr_chegaralarida_kesiladi():
    x = np.ones(SR * 10, np.float32)
    y = nutqni_kes(x, SR, [(10, 331), (341, 540)], "60/1")
    assert len(y) == round(520 * SR / 60)
    assert y[0] == 0 and y[len(y) // 2] == 1                        # ulanishda 5 ms fade


def test_normallashtirish_minus_14(tmp_path):
    t = np.arange(SR * 4) / SR
    x = (0.5 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    normallashtir(x, SR, tmp_path / "o.wav")
    y, sr = sf.read(tmp_path / "o.wav", dtype="float32")
    assert lufs(y, sr) == pytest.approx(-14, abs=0.5)
    assert 20 * np.log10(np.abs(y).max()) <= -1.4


def test_drop_vaqti():
    m = np.concatenate([0.01 * np.random.default_rng(0).standard_normal(SR * 3),
                        0.5 * np.random.default_rng(1).standard_normal(SR * 3)]).astype(np.float32)
    assert drop_vaqti(m, SR) == pytest.approx(3.0, abs=0.5)


def test_sfx_faqat_grafikaga(tmp_path):
    s = tmp_path / "pop.wav"
    sf.write(s, np.ones(1000, np.float32) * 0.1, SR)
    a = np.zeros(SR * 2, np.float32)
    with pytest.raises(ValueError, match="faqat grafikaga"):
        sfx_qosh(a.copy(), SR, [{"fayl": str(s), "t": 1.0}], grafika_vaqtlari=[])
    maska = np.ones(SR * 2, bool)                                      # nutq ustida -> -5 dB
    r = sfx_qosh(a.copy(), SR, [{"fayl": str(s), "t": 1.0}], [1.0], maska)
    assert r.max() == pytest.approx(0.1 * 10 ** (-5 / 20), rel=0.02)


@pytest.fixture
def sintetik(tmp_path):
    v = tmp_path / "v.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=1080x1920:r=30:d=2",
                    "-f", "lavfi", "-i", "sine=f=300:d=2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-c:a", "aac", str(v)],
                   check=True)
    o = tmp_path / "o.wav"
    t = np.arange(int(SR * 1.5)) / SR
    normallashtir((0.3 * np.sin(2 * np.pi * 300 * t)).astype(np.float32), SR, o)
    sahna = Sahna([PastkiGradient(0, 1.5), Subtitr(0.5, 1.5, "o‘g‘il ta’lim", US, chiqish_s=0.2)], 1.5, "30/1",
                  [(0, 20), (30, 55)])
    return SimpleNamespace(video=v), sahna, o, tmp_path


def test_render_tasdiqsiz_ishlamaydi(sintetik):
    lo, sahna, o, p = sintetik
    with pytest.raises(TasdiqYoq):
        render(lo, sahna, o, p / "n.mp4")
    assert not (p / "n.mp4").exists()


def test_render_va_tekshiruv(sintetik):
    lo, sahna, o, p = sintetik
    render(lo, sahna, o, p / "n.mp4", tasdiq=True)
    t = tekshir(lo, sahna, p / "n.mp4")
    assert t["kadrlar"] == 45 and t["olcham"] == "1080x1920"
    assert t["holat"] == "OK", t["xatolar"]
    assert max(abs(v) for v in t["rang_siljishi_yuv"].values()) < 1.5


def test_tekshiruv_rang_siljishini_ushlaydi(sintetik):
    lo, sahna, o, p = sintetik
    render(lo, sahna, o, p / "n.mp4", tasdiq=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(p / "n.mp4"), "-vf", "eq=brightness=0.04:saturation=1.3",
                    "-c:a", "copy", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                    str(p / "rangli.mp4")], check=True)
    t = tekshir(lo, sahna, p / "rangli.mp4")
    assert t["holat"] == "XATO" and any("rang siljishi" in x for x in t["xatolar"])
