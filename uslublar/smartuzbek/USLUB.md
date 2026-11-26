# SmartUzbek reels uslubi (tasdiqlangan: loyihalar/smartuzbek_01, v2)

Foydalanuvchi tasdiqlagan uslub. SmartUzbek uchun har yangi video SHU uslubda qilinadi.
Namuna kod va aktivlar: `loyihalar/smartuzbek_01/` (animatsiya.py, gapir.py, yuz_top.py, lab_sinov.py, fon.py).
Marketing rejasi: `loyihalar/smartuzbek_01/SmartUzbek_SMM_reja.pdf` (30 kunlik mavzular, 20–35 s, CTA).

## Kadr (1080x1920 koordinatalarida; render 4K 2160x3840, 60 fps)
- Fon: dasturda chiziladi (fon.py) — to'q ko'k gradient #02143C → #022B7A, markazda yumshoq nur, pol chizig'i sariq y≈1594.
- Personaj: ko'zoynakli jurnalist (stikerlar/poza/poza_1..6), PASTDA, oyoqlari y=1585, balandligi 720 px.
  Og'zi gapga mos qimirlaydi (vizemlar X/M/kichik/A/E/O, ovoz energiyasi + Whisper unlilari), ko'z qirpiydi
  (har 2.8–5 s, 0.12 s), ovoz kuchiga qarab yengil chayqaladi. Poza sahnaga qarab almashadi (pop bilan).
- Buyumlar: TEPADA, y ≈ 380–720, aytilgan so'z bilan pop (80→106→100%, 0.3 s) yoki uchib kiradi; sahna oxirida 0.25 s fade.
  Urg'u so'zda zoom 100→110% (tovushsiz). Stikerlar soyasiz (stiker_tozala.py buyum ... 0.002).
- Logo: oq yumaloq kartada (asl/logo.jpg); CTA da telefon ekranida.
- Harf kartalari: eski o‘ g‘ sh ch — oq; yangi ö ğ ş ç — sariq #FDC005, Inter Bold, navy harf.
- SUBTITR: B — KARAOKE. Pastda, y=1420 (personaj oyoqlari ustida), oq Oswald 600, ~64 px (maks. eni 720 px),
  to'q yarim shaffof karta (0,6,24 @ 170), aytilayotgan so'z tagida sariq chiziq (Whisper so'z boshi + 0.12 s).
  2–3 so'zli bo'laklar; matn tasdiqlangan ssenariydan, vaqt Whisper + RMS dan. Matn doim oq.
- Safe zona: x 150–930, y 230–1595 — renderdan oldin `python animatsiya.py tekshir` (piksel, butun video).

## Ovoz
- AI ovoz (foydalanuvchi yasaydi). Pauzalar: ovoz_qisqart.py (≥0.25 s → 0.12 s, ≥0.6 s → 0.25 s). Tezlashtirilmaydi
  (tabiiy tezlik; 36–37 s ham qabul qilingan).
- Whisper (large-v3) faqat so'z vaqtlari uchun; so'zlar soni ssenariy bilan solishtiriladi.
- Musiqa yo'q (litsenziya xavfi). SFX: BigSoundBank CC0 (pop, whoosh, hit), faqat grafikaga, gap ustida -5 dB.
- Yakuniy -14 LUFS, TP ≤ -1.5 dBFS.

## Brend
- Ranglar: navy #022B7A, sariq #FDC005, to'q sariq #FF9C01, oq.
- Ssenariy tuzilishi: hook (savol/muammo) → "Salom, men Smartbek!" → 3 sabab / yechim → "hozircha bepul" → CTA
  (botga kiring, kanalga obuna, do'stga yuboring). Funksiyalar e'lon qilinishidan oldin botda tekshirilsin (PDF qoidasi).

## Yangi video ish tartibi
1. Mavzu (PDF rejasidan) → ssenariy (≈80 so'z) + har gapda ekrandagi buyum; tasdiq.
2. Kerakli yangi buyumlar uchun ChatGPT promt (BUYUM_PROMT.md uslubida, bitta 4x2 setka, brend ranglari, matnsiz).
3. OVOZ_MATNI.txt (raqamlar so'z bilan, "Smart Uzbek" ajratib) → foydalanuvchi AI ovoz yasaydi.
4. ovoz_qisqart → Whisper → subtitr.py (SUBTITR_MATNI.txt, "SmartUzbek" qo'shib) → vaqt_chizigi.json (SFX).
5. animatsiya.py: SAHNALAR, POZALAR, ELEMENTLAR so'z vaqtlariga; `tekshir`; 4–7 sinov kadri → tasdiq.
6. Render 4K 60 fps (~6 daqiqa), videodan kadr olib tekshirish, yuborish. Instagram tavsifi.
