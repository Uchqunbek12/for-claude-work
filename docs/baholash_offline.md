# Baholash natijalari — offline (LLM'siz)

Sana: 2026-10-08  
Kirish: `samples/decompiled/*.angr.c` (angr dekompilyatori natijasi).

| Namuna | Psevdokodga ekvivalent | Asl kodga ekvivalent | Usullar topildi | Qatorlar (psevdo → natija → toza) | CC (psevdo → natija → toza) | Urinish | Narx | Vaqt |
|---|---|---|---|---|---|---|---|---|
| s1_mba | verified | ✅ | 100% | 10 → 10 → 4 | 1 → 1 → 1 | 1 | $0.00000 | 0.25 s |
| s2_opaque | verified | ❌ | 100% | 17 → 10 → 6 | 7 → 5 → 3 | 1 | $0.00000 | 0.21 s |
| s3_flatten | verified | ✅ | 100% | 28 → 12 → 6 | 7 → 2 → 2 | 1 | $0.00000 | 0.12 s |
| s4_strings | verified | ✅ | 100% | 9 → 10 → 4 | 2 → 2 → 1 | 1 | $0.00000 | 0.14 s |
| s5_combined | verified | ✅ | 100% | 42 → 18 → 8 | 9 → 2 → 2 | 1 | $0.00000 | 0.19 s |

**Jami:**

- Psevdokodga ekvivalentligi isbotlangan: **5/5**
- Haqiqiy asl kodga ekvivalent: **4/5**
- Usullarni aniqlash (o'rtacha recall): **100%**
- Tsiklomatik murakkablik: **26 → 12** (54% kamaydi)
- Qatorlar: **106 → 60** (43% kamaydi)
- Umumiy narx: **$0.00000**

Izoh: `s2_opaque` uchun angr dekompilyatori shartni xato soddalashtirgan (jurnal, 1.6-bo'lim). Agent psevdokodni etalon deb oladi, shuning uchun natija psevdokodga ekvivalent bo'lsa ham, asl kodga ekvivalent bo'lmasligi mumkin — bu dekompilyator xatosi, agentniki emas.
