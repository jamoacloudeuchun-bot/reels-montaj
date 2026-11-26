"""SmartUzbek brend foni (dasturda chiziladi, har qanday o'lchamda tiniq): to'q ko'k gradient,
yumshoq radial nur (CLAUDE.md: solid + radial Ramp + Screen usulida), pastda "pol" chizig'i.
Shape layer'da blur/soya yo'q."""
import numpy as np
from PIL import Image

KOK_TOQ = np.array([2, 20, 60])       # #02143C
KOK = np.array([2, 43, 122])          # #022B7A (logo)
NUR = np.array([40, 110, 230])


def fon(W=1080, H=1920):
    y = np.linspace(0, 1, H)[:, None, None]
    x = np.linspace(0, 1, W)[None, :, None]
    g = KOK_TOQ * (1 - y) + KOK * y                      # vertikal gradient
    # radial nur (Screen): markaz y~0.42
    r = np.sqrt(((x - 0.5) / 0.75) ** 2 + ((y - 0.42) / 0.5) ** 2)
    nur = np.clip(1 - r, 0, 1) ** 2 * 0.55
    g = 255 - (255 - g) * (1 - nur * NUR / 255)
    # pol: pastki 17% biroz och, chegarasida sariq ingichka chiziq
    pol = y > 0.83
    g = np.where(pol, g * 0.85 + np.array([10, 25, 60]) * 0.15, g)
    im = np.broadcast_to(g, (H, W, 3)).copy()
    chiziq = int(0.83 * H)
    im[chiziq:chiziq + max(2, H // 640)] = [253, 192, 5]
    return Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)).convert("RGBA")


if __name__ == "__main__":
    fon().save("kesh/fon_sinov.png")
