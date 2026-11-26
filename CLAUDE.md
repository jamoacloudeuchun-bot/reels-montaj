# Montaj qoidalari (CLAUDE.md)

> Bu faylni montaj papkangizga `CLAUDE.md` nomi bilan qo'ying. Claude Code shu papkada ochilganda har safar o'qiydi.
> Raqamlar 1080x1920 vertikal reels uchun. Har biri real montajda "bunday qilma" deb tuzatilgandan keyin yozilgan.

## Umumiy
- Javoblar o'zbek tilida (lotin), "siz" deb. Nima tekshirilganini va nima taxmin ekanini aniq ayt.
- Render faqat tasdiqdan keyin. Avval 3–4 ta kadrni ko'rsat, "yaxshi" desam keyin render.
- Pullik generatsiya (rasm, video, ovoz) faqat ruxsat bilan: avval model va narxni ayt. Kredit tugasa boshqa servisga o'zing o'tma, so'ra.
- Faktlarni uydirma: ekrandagi yozuv va raqamlar gapdan chiqsin. O'zing qo'shgan narsa bo'lsa, hisobotda ayt.

## Joylashuv (Instagram safe zona)
- Hamma matn va kartalar: **x 150–930, y 230–1595**. Markazdagi matn eni ≤ 720–780 px.
- Yon kartalar chap chetdan ~x 80 dan boshlanishi mumkin (hammasini markazga taqama).
- Talking-head: matnli hook ≈ **y 420**, ko'zlar ≈ **y 810** (kerak bo'lsa videoni 120–130% kattalashtir), subtitr ≈ **y 1260**.
- Yuzli qismlarda pastdan tepaga yumshoq qoraytirish gradienti mumkin (0.55 @ 70%), lekin kuchli emas.
- Split ekranni (ikkiga bo'lish) kam ishlat: ro'yxat/sanash qismlarini to'liq ekran grafikada qil.
- Grafikani qurgach, kadrga safe zona ramkasini chizib (ffmpeg drawbox) tekshir.

## Matn
- Video ustidagi hamma matn **oq**. Rangli teg va rangli aksent so'z ham oq.
- Harf orasi (tracking) oddiy: 0…20. Keng tracking (200+) yo'q.
- Izohlar kichik va xira bo'lmasin: oq, 100% opacity, ~44 px.
- Sarlavhaga drop shadow qo'yma. O'qilishi uchun pastki qoraytirish ishlat.
- Bir so'z bir vaqtda faqat bitta joyda (yo sarlavhada, yo grafikada).
- Logotiplar katta (140–200 px plitka) va vektor: LobeHub icons yoki Simple Icons. Rasmdan kesib kattalashtirma, xira chiqadi.

## Subtitr
- Whisper o'zbekchani yomon o'qiydi: undan faqat **so'z vaqtlari** ol, matnni gapdan mantiqan tozalab yoz va tasdiqlat.
- Whisper vaqtlari ~0.4–0.5 s oldinda chiqadi: kesish va subtitr vaqtini ovoz energiyasidan (RMS, 25 ms) aniqla.
- Aniq eshitilmagan joyga taxminiy matn yozma, ochiq ayt.

## Kesish
- Gap boshi va oxirini maksimal taqab kes: boshidan ~0.05 s, oxiridan ~0.08 s qoldir. Gap tugagach uzun "zazor" qolsa, ko'z chetga ketgani ko'rinadi.
- Ichki 0.25 s+ pauzalarni ~0.12 s ga qisqartir.
- Kesimlarni kadr raqami bilan qil (aks holda ovoz va video siljiydi).
- Shovqinli ovozni DeepFilterNet bilan tozala, gapni -42 dB chegarasi bo'yicha top.

## Rang
- Kamera videosi **o'z rangida** qoladi. Men aytmagunimcha rang berilmaydi.
- So'rasam ham to'yinganlik va kontrastni ko'tarma: avval juda yengil variantni bitta kadrda (asl / yangi) ko'rsat va tasdiq ol.

## Ovoz
- Musiqa: `-12 dB` atrofida (≈ -21 LUFS), ovoz tagida pasayadi (ducking). Yakuniy -14 LUFS.
- SFX faqat grafikaga (pop, whoosh, hit), sarlavha va subtitrga yo'q. Gap ustiga chiqqan SFX'ni -5 dB qil.
- Haqiqiy yozilgan SFX ishlat (sintez emas). Oyna sinishi kabi qo'pol tovushlar ishlatilmaydi.
- Musiqa boshlanish soniyasi aytilmasa: trekdagi zarbani (drop) videoning asosiy momentiga to'g'rila.

## Animatsiya
- Kirish: pop 80→106→100% (0.2–0.34 s), matn pastdan ~36 px ko'tarilib 0.2 s fade. Chiqish 0.2–0.3 s fade.
- Zoom zarbasi faqat ta'kid so'zda (100→109–111%, 0.3 s kirish, 0.35 s chiqish), tovushsiz.
- Shape layer'da blur/soya ishlatma (chetidan kesiladi). Nur kerak bo'lsa: butun kadrli solid + radial Ramp + Screen.

## Loyiha uslublari
- SmartUzbek videolari: tasdiqlangan uslub va ish tartibi — `uslublar/smartuzbek/USLUB.md` (har yangi SmartUzbek videosida shunga amal qil).
