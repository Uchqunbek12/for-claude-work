# Baholash: Claude Sonnet 5.5 (haqiqiy API, 5 ta funksiya)

Sana: 2026-11-04. Model: `claude-sonnet-5-5`, effort: `medium`, kesh o'chirilgan (`--no-cache`), tekshiruv: gcc +
differensial test (2000 tasodifiy kirish), kirish: `samples/decompiled/*.angr.c`. Yurgizilgan joyi: loyiha papkasi
(CLI va Web UI).

| Funksiya (namuna) | Natija | Urinish | Chiqish tokeni | Narx | Vaqt | Qatorlar | Murakkablik | Claude bergan nom |
|---|---|---|---|---|---|---|---|---|
| `gcd` (s3_flatten) | Tasdiqlandi | 1 | 2067 | $0.0345 | 23.2 s | — | 7 → 2 | `gcd` |
| `checksum` (s5_combined) | Tasdiqlandi | 1 | 2383 | $0.0392 | 23.9 s | — | 9 → 2 | `fnv1a_checksum` |
| `rotl32` (s7_calls) | Tasdiqlandi | 1 | 1311 | $0.0256 | 15.0 s | — | 1 → 1 | `rotate_left_32` |
| `rot_hash` (s7_calls) | Tasdiqlandi | 1 | 1979 | $0.0346 | 20.4 s | — | 8 → 2 | `rot_hash` |
| `bubble_sort` (s8_sort, Web UI) | Tasdiqlandi (1690 test) | 1 | — | $0.0243 | 24.2 s | 50 → 10 | 16 → 5 | `bubble_sort` |

**Jami:** 5 funksiya, hammasi 1-urinishda «Tasdiqlandi»; narx **$0.024–0.039** (o'rtacha ≈ **$0.032**) / funksiya; vaqt 15–24 s.

## Nimani kuzatdik

* **Kod to'g'ri va tekshiruvdan o'tdi**: gcd — Evklid `while (b != 0)`, checksum — FNV-1a (`2166136261u`, `16777619u`), `bubble_sort` — ichma-ich
  `for`; `rot_hash` yordamchi `rotl32` ni **asl nomi bilan** chaqirgan (prompt qoidasi ishladi).
* **Tushuntirishlar**: har bir blokda sarlavha, mutaxassis izohi va «oddiy tilda» matn bor; oddiy matnda kod belgilari yo'q.
  Masalan, gcd: «Ikkinchi son birinchi o'rinni egallaydi, qoldiq esa ikkinchi o'ringa o'tadi».
* **Web UI** (Chromium): «Kalitni tekshirish» tugmasi ishladi, natija, bloklar, «Oddiy tilda» ko'rinishi to'g'ri chiqdi.

## Cheklovlar (halol)

* **Kichik tanlama:** 5 funksiya, 4 namuna (s1_mba, s2_opaque, s4_strings, s6_buffer yurgizilmadi). To'liq baholash:
  `deobf eval --model sonnet -o docs/baholash_sonnet.md` (8 namuna, taxminan $0.3).
* **Xato tuzatish sikli haqiqiy Claude bilan ko'rilmadi:** hamma natija 1-urinishda to'g'ri chiqdi, shuning uchun
  "xatoni qaytarib qayta so'rash" qismi faqat soxta mijoz bilan sinalgan.
* **Narx** faqat `medium` effort va shu namunalar uchun; murakkabroq kodda yoki `high` effortda ko'proq bo'ladi.
* **Rad etish (`cyber`)** haqiqiy zararli dastur kodida sinalmagan.
* Prompt keshi ($0.20 / 1M o'qish) bu yurgizishlarda ishlamagan (tuzatish urinishi bo'lmadi).
