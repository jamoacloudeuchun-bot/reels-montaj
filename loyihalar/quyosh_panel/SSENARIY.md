# Quyosh paneli: 3 sabab (Reels, ~37 s, kamerasiz, stiker-animatsiya)

## Ovoz matni (92 so'z, tasdiq kutilmoqda)
1. Har oy svet uchun pul to'laysiz. Quyosh esa tepada turib, har kuni tekin nur beradi!
2. Salom, men Quyoshvoy! Quyosh panelini qo'ydirish uchun 3 ta sabab.
3. Birinchi: svet puli kamayadi. Kunduzi uyingiz elektrni o'zi ishlab chiqaradi, oy oxiridagi hisob esa sezilarli kichrayadi.
4. Ikkinchi: svet o'chsa ham qorong'ida qolmaysiz. Akkumulyator bilan muzlatgich, chiroq va internet ishlayveradi.
5. Uchinchi: bu xarajat emas, sarmoya. Panel bir marta o'rnatiladi, tejalgan pul esa uning narxini asta-sekin qoplaydi.
6. Bizda quyoshli kunlar ko'p — undan foydalanmaslik isrof!
7. Qaysi sabab siz uchun muhimroq? Izohda yozing va uyida hali paneli yo'q do'stingizga yuboring!

Eslatma: 4-gap faqat akkumulyatorli (gibrid) tizimga to'g'ri. Aniq raqamlar (foiz, qoplash muddati) ataylab yo'q.

## Personaj: Quyoshvoy
Dumaloq sariq-to'q sariq quyosh, yumaloq uchli nurlar, katta ko'zlar, pushti yonoqlar,
peshonada qora ko'zoynak, ko'kragida ko'k panel nishoni, oq qo'lqop, ko'k krossovka.

## Aktivlar holati
- `asl/chatgpt_v1_umumiy.png` — ChatGPT 1-urinish (hammasi bitta 1254 px rasmda).
- `stiker_kes.py` — oq fondan shaffof PNG kesish.
- `sinov_kadrlar.py` — 4 ta sinov kadri (render emas), `korik/sinov_varaq_v1.png`.
- Muammo: stikerlar ~270 px, kadrda 2–3 marta kattalashtiriladi (yumshoq chiqadi).
  Kerak: har setka alohida, katta o'lchamda (1024+ px).
- Tungi fonda hamma uy yoniq — 2-sabab uchun bitta uy yoniq bo'lishi kerak.

## Personaj v2 (2-urinish)
- `asl/chatgpt_v2_personaj.png` (1238x1271), kesilgani `stikerlar/personaj/personaj_1..6.png` (~550 px).
  1 qo'l silkitish, 2 pastga ko'rsatish, 3 ko'z qisish, 4 ko'zoynak (XATO: ikki juft ko'zoynak), 5 xursand sakrash, 6 o'ylanish.
- Yetishmaydi: "hayron" pozasi. 4-poza qayta yasalishi kerak.
- Kesish: `python stiker_kes.py <rasm> <papka> personaj --setka 3x2`.

## Qarorlar
- Videoda hech qanday yozuv va raqam yo'q (foydalanuvchi qarori). `sinov_kadrlar.py` da MATN = False.
- Ovoz: AI (TTS). Matn: `OVOZ_MATNI.txt` (raqamlar so'z bilan).
