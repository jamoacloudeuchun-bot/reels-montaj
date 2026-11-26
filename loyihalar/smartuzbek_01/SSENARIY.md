# SmartUzbek: botni sinab ko'rish uchun 3 sabab (Reels, ~30 s, kamerasiz, stiker-animatsiya)

Manba: SmartUzbek_SMM_reja.pdf (26-kun mavzusi: "Nega SmartUzbek'ni sinab ko'rishingiz kerak?").
Maqsad: botga foydalanuvchi + kanalga obunachi. Format: Quyosh paneli loyihasidagi kabi
(personaj pastda, buyumlar tepada, subtitr tepada, safe zona, 4K 60 fps).

## Ovoz matni (79 so'z, tasdiq kutilmoqda)
1. Bir soatlik ovozli yozuvni qo‘lda matnga ko‘chirasizmi? Bu soatlab vaqt oladi!
2. Salom, men Smartbek! SmartUzbek botini sinab ko‘rish uchun uchta sabab.
3. Birinchi: ovozli xabarni botga yuborasiz, u matnga aylanadi. Talaba, jurnalist, bloger — hammaga qulay.
4. Ikkinchi: matningizdagi imlo xatolarini tuzatib beradi. Endi xato bilan yuborishdan uyalmaysiz.
5. Uchinchi: eski yozuvdagi matnni yangi yozuvga o‘tkazadi — yangi harflar bilan.
6. Hammasi bitta Telegram botda va hozircha bepul!
7. Profildagi havola orqali botga kiring va sinab ko‘ring. Foydali bo‘lsa, kanalga obuna bo‘ling va do‘stingizga yuboring!

## Tekshirish kerak (PDF "Muhim qoida")
- Imlo tuzatish va eski -> yangi yozuv funksiyalari botda amalda tekshirilsin, keyin e'lon qilinsin.
- Bot havolasi / username va SmartUzbek logotipi fayli kerak.

## Personaj: jurnalist (tanlangan)
- asl/jurnalist_pozalar.png -> stikerlar/poza/poza_1..6 (salom, pastga ko'rsatish, bosh barmoq, o'ylash, sakrash, ikki qo'l ochiq).
- yuz_top.py -> yuz.json (har pozada og'iz va ko'z joyi, avtomatik).
- gapir.py: og'iz vizemlari (X, M, kichik, A, E, O) + ko'z qirpish; lab_sinov.vizem_chizigi ovoz+Whisper bo'yicha.

## Ovoz va animatsiya (v1)
- asl/ovoz_ai_v1.wav (44.1 s) -> pauzalar qisqartirildi (36.3 s) -> atempo 1.06 = 34.25 s (+0.7 s dum = 34.95 s).
- Whisper: 82 so'z, ssenariy bilan to'liq mos (sozlar_whisper.json). Subtitr: subtitr.json (35 bo'lak, "SmartUzbek" qo'shib).
- vaqt_chizigi.json: 22 SFX. Yakuniy ovoz -14.2 LUFS, TP -1.6.
- animatsiya.py: brend fon, gapiruvchi jurnalist, buyumlar, logo karta, ö ğ ş ç kartalari. Piksel safe zona: 0 ta chiqish.
