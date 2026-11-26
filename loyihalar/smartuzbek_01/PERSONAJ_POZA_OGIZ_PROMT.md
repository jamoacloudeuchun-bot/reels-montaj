# Jurnalist (tanlangan 6-variant): pozalar, og'iz va ko'z qirpish uchun promtlar

Lip-sync usuli: har pozada asl og'iz o'chiriladi, o'rniga og'iz shakli (vizem) qo'yiladi; vizem ovoz
energiyasi + Whisper so'z vaqtlari (unli harf) bo'yicha tanlanadi. Sinov: lab_sinov.py.

## 1-promt: pozalar (har biri alohida rasm)
```
Use the attached journalist character (round glasses, navy blazer, white shirt, yellow lanyard with a blank badge, handheld microphone) as the exact reference. Same face, same hair, same glasses, same colors, same flat 2D cartoon style with thick dark navy outline. No blur, no drop shadow, no white sticker border.

Create 6 SEPARATE images, one pose per image, 1024x1536 portrait, TRANSPARENT background, full body from head to shoes, character centered and filling about 90% of the height.

VERY IMPORTANT for every pose:
- The HEAD is always facing straight to the camera, upright, not tilted, not turned, same size and same position in the image.
- The MOUTH is CLOSED with a small gentle smile (a simple curved line). No open mouth, no teeth.
- Nothing covers the face, the mouth area must be fully visible.
- Absolutely NO text, letters, numbers or logos anywhere (the badge stays blank).

Poses:
1. waving hello with the free hand, microphone in the other hand
2. pointing down with the index finger
3. thumbs up, other hand holds the microphone
4. thinking: hand near chin (not covering the mouth), eyes looking up
5. happy jump, both arms up, microphone in one hand
6. surprised: eyebrows raised, both hands open at shoulder level

Make pose 1 first, then continue with the next pose each time I write "next".
```

## 2-promt: og'iz shakllari (bitta rasm)
```
Same character, same style. Create ONE image, square 1536x1536, TRANSPARENT background: a 3x2 grid of 6 isolated MOUTHS only (no face, no skin, no head), all exactly the same size and drawn for this character's face, thick dark navy outline, dark red mouth inside, white top teeth, pink tongue, front view.
1. closed gentle smile (a curved line)
2. lips pressed together (for M, B, P)
3. slightly open (small)
4. wide open "A"
5. wide flat open showing top teeth "E / I"
6. small round "O / U"
No text, no letters, no labels.
```

## 3-promt: ko'z qirpish (bitta rasm)
```
Same character, same style. ONE image, TRANSPARENT background: only the upper face area of the character (eyebrows, glasses, eyes, nose bridge — no mouth), straight front view, same size as in the poses, with the EYES CLOSED (gentle curved lines behind the glasses). No text.
```
