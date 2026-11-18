# Andoza_01 — tahlil

> Manba: foydalanuvchi yuborgan namuna reels (720×1280, 30 fps, 77.5 s, H.264, AAC 44.1 kHz).
> Asl video **repoga qo'shilmaydi** — faqat shu tahlil, `uslub.json` va `kadrlar/` saqlanadi.
> **CLAUDE.md asosiy qoida.** Bu andoza faqat tuzilish va ritm uchun namuna; ziddiyat bo'lsa CLAUDE.md ustun.

Belgilar: **[o'lchandi]** — asbob bilan o'lchangan; **[ko'rildi]** — kadrlardan ko'rib aniqlangan; **[taxmin]** — tasdiqlanmagan.

## 1. Montaj ritmi
- Kamera (V) va to'liq ekran grafika (G) navbatma-navbat, har bo'lak o'rtacha **3–5 s**. [o'lchandi]
  `V 0–5.25 · G 5.25–10.75 · V 10.75–13.5 · G 13.5–18 · V 18–19.75 · G 19.75–26.5 · V 26.5–26.75 · G 26.75–30 · V 30–30.5 · G 30.5–32 · V 32–34.75 · G 34.75–36.75 · V 36.75–38.75 · G 38.75–43.5 · V 43.5–45.25 · G 45.25–49.75 · V/foto-kartochka 49.75–60.5 · G 60.5–65.75 · V 65.75–74.75 · brend kartochka 74.75–77.25`
- Grafika vaqtning ~yarmi. Almashish gap bo'lagi (jumla) tugashiga to'g'ri keladi. [ko'rildi]
- Nutq vaqtning ~84 %, temp ~2.5–3 so'z/s. [o'lchandi]
- Kesimlar asosan keskin (hard cut); grafika chiqishida motion-blur bilan surilish bor. [ko'rildi]

## 2. Matn va "subtitr"
- Klassik so'zma-so'z subtitr **yo'q**. Gapning kalit so'zlari grafika sifatida chiqadi (sarlavha, raqam, ro'yxat). [ko'rildi]
- Shrift: tor (condensed) qalin bosh harflar — Oswald / Bebas Neue'ga o'xshaydi. [taxmin]
- Ba'zi sarlavhalar kursiv serif + soya. [ko'rildi]
- Ierarxiya: kichik yorliq (masalan "1-BOSQICH") → katta sarlavha → kartochka ichidagi matn. [ko'rildi]

## 3. Grafik elementlar
- **Fon:** to'q ko'k vertikal gradient (~#0F1E3D tepada → #0C1934 o'rtada), ustida ingichka yoy chiziqlar va pastda perspektiv to'r. [o'lchandi/ko'rildi]
- **Lower-third (kamera ustida):** to'q ko'k (#070E24) yumaloq kartochka, ingichka chegara; chapda oltin (#E6AD49) ikonka plitkasi; tepada kichik yorliq, pastda katta so'z. 1080×1920 da ≈ **x 90–990, y 1155–1380**. [o'lchandi]
- **Kontent kartochka:** #212E4B atrofidagi yarim shaffof kartochka, ikonka + matn + chiziqlar + ✓. [o'lchandi]
- **Ro'yxat/qadamlar:** raqamli doira + nom + o'ngda oltin ✓; bajarilgan qadam ustidan chiziladi; pastda oltin "pill" tugma. [ko'rildi]
- **Raqam grafikasi:** katta raqam + shkala (17→22), sana kartochkalari (oy nomi oltin sarlavhali), doira ichida raqam. [ko'rildi]
- **Hook:** xiralashtirilgan video ustida rasmli kartochka + katta sarlavha, harflar ketma-ket chiqadi (0.75–2.75 s). [ko'rildi]

## 4. Animatsiya va motion
- Matn: harflar ketma-ket pastdan ko'tariladi, blur → aniq. [ko'rildi]
- Kartochkalar suzib kiradi; ✓ belgilar birin-ketin; raqam/shkala harakatlanadi. [ko'rildi]
- Kamera kadrlarida qo'lda harakat (qiya kadr), ehtimol yengil push-in. [taxmin]

## 5. Ovoz
- Integral −14.1 LUFS, LRA 2.2, peak −2.9 dBFS. [o'lchandi]
- Fon musiqasi butun video bo'yi; gap paytida nutqdan **~12 dB past**, pauzada faqat ~2.5 dB ko'tariladi (yengil ducking). [o'lchandi, DeepFilterNet bilan ajratib]
- Temp ~85 BPM, sokin korporativ xarakter. [taxmin]
- ~30 ta keskin fon zarbasi, ko'pi grafika almashuviga to'g'ri keladi (5.9, 13.9, 19.75, 26.8, 45.2, 49.0 s …) — whoosh/pop SFX bo'lishi mumkin. [taxmin]

## 6. Rang
- Kamera kadri iliq "oltin soat", kontrast va to'yinganlik yuqori — rang berilganga o'xshaydi. [ko'rildi]

## 7. CLAUDE.md bilan moslashtirish (foydalanuvchi qarori)
| Andozada | Bizda (CLAUDE.md asosida) |
|---|---|
| Oltin yorliq/raqam/aksent matn | **Barcha matn oq.** Oltin faqat grafik element, ikonka va ✓ belgilarda |
| Keng tracking (≈200+) yorliqlarda | Tracking 0…20 |
| Sarlavhalarda soya | Soya yo'q; o'qilishi uchun pastki qoraytirish |
| Iliq rang ishlovi | Kamera videosi o'z rangida |
| Blur bilan chiqadigan harf/kartochka | Shape layer'da blur yo'q; kirish: pop 80→106→100 %, matn 36 px ko'tarilib 0.2 s fade |
| Kursiv serif sarlavha | Ishlatilmaydi (bitta oilaviy shrift) |

## 8. Ko'chirilmaydi
Andozadagi matnlar, DXX / QALQON AKADEMIYASI logotiplari va nomlari, foto kartochkalar, oxirgi brend kartochkasi.

## 9. Shrift tekshiruvi (o'rnatilmagan, faqat fayl ichi tekshirildi)
| Shrift | ‘ U+2018 | ’ U+2019 | ʻ U+02BB | ʼ U+02BC | Kichik harf |
|---|---|---|---|---|---|
| Oswald (Google Fonts, OFL) | ✓ | ✓ | ✓ | ✓ | bor |
| Bebas Neue (Google Fonts, OFL) | ✓ | ✓ | **✗** | ✓ | **yo'q** (faqat bosh harf) |

Tavsiya: **Oswald** — barcha o'zbekcha belgilar bor. Bebas Neue'da ʻ (U+02BB) yo'q; faqat ‘ (U+2018) bilan yozilsa ishlaydi.
