# Baholash natijalari — model: deepseek-flash

Sana: 2026-11-16  
Kirish: `samples/decompiled/*.angr.c` (angr dekompilyatori natijasi).

| Namuna | Psevdokodga ekvivalent | Asl kodga ekvivalent | Usullar topildi | Qatorlar (psevdo → natija → toza) | CC (psevdo → natija → toza) | Urinish | Narx | Vaqt |
|---|---|---|---|---|---|---|---|---|
| s1_mba | verified | ✅ | 100% | 10 → 10 → 4 | 1 → 1 → 1 | 1 | $0.00179 | 8.87 s |
| s2_opaque | verified | ❌ | 100% | 17 → 7 → 6 | 7 → 5 → 3 | 2 | $0.00971 | 36.27 s |
| s3_flatten | verified | ✅ | 100% | 28 → 9 → 6 | 7 → 2 → 2 | 1 | $0.00232 | 11.27 s |
| s4_strings | verified | ✅ | 100% | 9 → 14 → 4 | 2 → 2 → 1 | 1 | $0.00182 | 9.27 s |
| s5_combined | verified | ✅ | 100% | 42 → 12 → 8 | 9 → 2 → 2 | 1 | $0.00291 | 13.72 s |
| s6_buffer | verified | ✅ | 100% | 31 → 7 → 5 | 8 → 2 → 2 | 1 | $0.00301 | 14.98 s |
| s7_calls | verified | ❌ | 100% | 29 → 6 → 9 | 8 → 2 → 2 | 1 | $0.00261 | 12.62 s |
| s8_sort | verified | ✅ | 100% | 50 → 16 → 10 | 16 → 5 → 5 | 1 | $0.00383 | 18.89 s |

**Jami:**

- Psevdokodga ekvivalentligi isbotlangan: **8/8**
- Haqiqiy asl kodga ekvivalent: **6/8**
- Usullarni aniqlash (o'rtacha recall): **100%**
- Tsiklomatik murakkablik: **58 → 21** (64% kamaydi)
- Qatorlar: **216 → 81** (62% kamaydi)
- Umumiy narx: **$0.02801**

Izoh: `s2_opaque` uchun angr dekompilyatori shartni xato soddalashtirgan (jurnal, 1.6-bo'lim). Agent psevdokodni etalon deb oladi, shuning uchun natija psevdokodga ekvivalent bo'lsa ham, asl kodga ekvivalent bo'lmasligi mumkin — bu dekompilyator xatosi, agentniki emas.

---

## O'lchov sharoiti va xulosalar (qo'lda qo'shilgan izoh)

* **Qanday o'lchandi.** `deobf eval -m deepseek`, bo'sh kesh bilan (`.deobf_cache` o'chirilgan), haqiqiy DeepSeek API'si, `medium` chuqurlik. Sana: 2026-11-16.
  Model `deepseek-flash` (DeepSeek-V4.1-Flash). Narx **band soat** tarifida hisoblangan (bo'sh soatlarda yarmi), ya'ni yuqori chegara.
* **8/8 tasdiqlandi.** 7 tasi 1-urinishda; `s2_opaque` 2-urinishda: 1-urinishda model funksiyani «odatdagi clamp» deb o'ylab, psevdokoddagi juft/toq
  tekshiruvini tashlab yuborgan, tekshiruv buni ushladi, 2-urinishda (o'ylash yoqilgach) to'g'ri chiqdi. Offline zaxira kerak bo'lmadi.
* **Narx.** Jami **$0.028**, funksiyasiga o'rtacha ≈ **$0.0035** (Claude Sonnet ≈ $0.032: taxminan 10 baravar arzon). Vaqt: 8–36 soniya.
* **«Asl kodga ekvivalent» 6/8** oldingi o'lchovlar bilan bir xil: `s2_opaque` va `s7_calls` da angr dekompilyatori **o'zi** xato qilgan (jurnal, 1.6-bo'lim).
* **Chuqurlik bo'yicha qo'shimcha o'lchov** (faqat `s2_opaque`, bir marta): Flash o'ylashsiz — 3 marta xato (oldingi standart); Flash + o'ylash — 1-urinishda, $0.0049, 17 s;
  Pro o'ylashsiz — 1-urinishda, $0.0139, 22 s; Pro + o'ylash — 1-urinishda, $0.0583, **132 s**. Shu sababli standart: 1-urinish o'ylashsiz, tuzatishda o'ylash.
* **Cheklov.** Tanlama kichik (8 namuna, har biri bir marta); modelning javoblari har safar bir xil bo'lmasligi mumkin (`s2_opaque` ikki marta takrorlanganda ikkalasida ham 2-urinishda to'g'ri chiqdi).
