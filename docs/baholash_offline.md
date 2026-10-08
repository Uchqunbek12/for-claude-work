# Baholash natijalari — offline (LLM'siz)

Sana: 2026-10-08  
Kirish: `samples/decompiled/*.angr.c` (angr dekompilyatori natijasi).

| Namuna | Psevdokodga ekvivalent | Asl kodga ekvivalent | Usullar topildi | Qatorlar (psevdo → natija → toza) | CC (psevdo → natija → toza) | Urinish | Narx | Vaqt |
|---|---|---|---|---|---|---|---|---|
| s1_mba | verified | ✅ | 100% | 10 → 10 → 4 | 1 → 1 → 1 | 1 | $0.00000 | 0.4 s |
| s2_opaque | verified | ❌ | 100% | 17 → 10 → 6 | 7 → 5 → 3 | 1 | $0.00000 | 0.34 s |
| s3_flatten | verified | ✅ | 100% | 28 → 12 → 6 | 7 → 2 → 2 | 1 | $0.00000 | 0.23 s |
| s4_strings | verified | ✅ | 100% | 9 → 10 → 4 | 2 → 2 → 1 | 1 | $0.00000 | 0.22 s |
| s5_combined | verified | ✅ | 100% | 42 → 18 → 8 | 9 → 2 → 2 | 1 | $0.00000 | 0.4 s |
| s6_buffer | verified | ✅ | 100% | 31 → 10 → 5 | 8 → 2 → 2 | 1 | $0.00000 | 0.39 s |
| s7_calls | verified | ❌ | 100% | 29 → 11 → 9 | 8 → 2 → 2 | 1 | $0.00000 | 0.31 s |
| s8_sort | verified | ✅ | 100% | 50 → 19 → 10 | 16 → 5 → 5 | 1 | $0.00000 | 1.42 s |

**Jami:**

- Psevdokodga ekvivalentligi isbotlangan: **8/8**
- Haqiqiy asl kodga ekvivalent: **6/8**
- Usullarni aniqlash (o'rtacha recall): **100%**
- Tsiklomatik murakkablik: **58 → 21** (64% kamaydi)
- Qatorlar: **216 → 100** (54% kamaydi)
- Umumiy narx: **$0.00000**

Izoh: `s2_opaque` uchun angr dekompilyatori shartni xato soddalashtirgan (jurnal, 1.6-bo'lim). Agent psevdokodni etalon deb oladi, shuning uchun natija psevdokodga ekvivalent bo'lsa ham, asl kodga ekvivalent bo'lmasligi mumkin — bu dekompilyator xatosi, agentniki emas.
