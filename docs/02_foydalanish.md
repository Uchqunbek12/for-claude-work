# 02. Foydalanish yo'riqnomasi (qadam-baqadam)

Bu yo'riqnoma Windows uchun yozilgan. Linux/macOS'da buyruqlar deyarli bir xil:
`.venv\Scripts\activate` o'rniga `source .venv/bin/activate` ishlatiladi.

---

## 1. Kerakli dasturlarni o'rnatish

| Dastur | Nima uchun | Qayerdan |
|---|---|---|
| **Python 3.10+** | vositaning o'zi | <https://www.python.org/downloads/> — o'rnatishda **"Add python.exe to PATH"** belgisini qo'ying |
| **Git** (ixtiyoriy) | repozitoriyni yuklab olish | <https://git-scm.com/> yoki GitHub'dan ZIP qilib yuklab oling |
| **gcc** (tavsiya etiladi) | natijani tekshirish (kompilyatsiya + differensial test) | MSYS2: <https://www.msys2.org/>, so'ng `pacman -S mingw-w64-ucrt-x86_64-gcc` va `C:\msys64\ucrt64\bin` ni PATH ga qo'shing |
| **IDA Free** yoki **Ghidra** | psevdokod olish | IDA Free: <https://hex-rays.com/ida-free/>, Ghidra: <https://ghidra-sre.org/> |

> gcc bo'lmasa ham vosita ishlaydi, faqat natija "tekshirilmadi" (⚪) deb belgilanadi.
> Eng ishonchli yo'l — **WSL** (Windows ichidagi Linux): `wsl --install`, so'ng `sudo apt install gcc python3-venv`.

Tekshirish (yangi terminal oynasida):
```bat
python --version
gcc --version
```

## 2. Loyihani o'rnatish

```bat
git clone https://github.com/Uchqunbek12/for-claude-work.git
cd for-claude-work
git checkout claude/vibrant-heisenberg-teie45

python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

Tekshirish — barcha testlar o'tishi kerak:
```bat
python -m pytest -q
```

## 3. Claude API kalitini olish (bir martalik)

1. <https://console.anthropic.com> saytida ro'yxatdan o'ting.
2. **Billing** bo'limida balansni to'ldiring (minimal summa yetarli: Haiku bilan 1 ta funksiya ≈ **$0.001**).
3. **API Keys → Create Key** — kalitni nusxalang (`sk-ant-...`). Kalit faqat bir marta ko'rsatiladi.
4. Loyiha papkasida `.env` nomli fayl yarating va unga yozing:
   ```
   ANTHROPIC_API_KEY=sk-ant-...sizning-kalitingiz...
   ```

> ⚠️ `.env` fayli `.gitignore` da, ya'ni GitHub'ga yuklanmaydi. Kalitni hech qachon kod ichiga
> yozmang va hech kimga yubormang.

API kalitsiz ham ishlash mumkin: `--offline` rejimi bepul (statik tahlil + avtomatik soddalashtirish).

## 4. Psevdokodni olish

### 4.1. IDA Free (eng oddiy yo'l — nusxalash)
1. IDA Free'da binar faylni oching (masalan, `samples/bin/s3_flatten.elf`).
2. Chap tomondagi **Functions** ro'yxatidan funksiyani tanlang (masalan, `gcd`).
3. **F5** bosing — psevdokod oynasi ochiladi.
4. Psevdokod oynasida **Ctrl+A**, keyin **Ctrl+C**.
5. Natijani faylga saqlang (masalan, `gcd.ida.c`) yoki to'g'ridan-to'g'ri Web UI'ga joylang.

**Global ma'lumotlar** (masalan, shifrlangan satr baytlari, `byte_4010` kabi nomlar):
nomni ikki marta bosing → baytlarni belgilang → **Shift+E** → "C unsigned char array" → natijani
psevdokod oxiriga qo'shing. Shunda vosita satrni ochib bera oladi va kodni to'liq sinay oladi.

> IDA Pro/Home bo'lsa: **File → Script file → `scripts/ida_export.py`** — barcha funksiyalar avtomatik saqlanadi.

### 4.2. Ghidra
- **Qo'lda:** funksiyani tanlang → **Decompile** oynasida o'ng tugma → *Export* yoki matnni belgilab nusxalang.
- **Skript bilan:** Script Manager → `scripts/ghidra_export.java` → ishga tushiring.
- **Avtomatik (headless):**
  ```bat
  analyzeHeadless C:\ghidra_proj demo -import samples\bin\s3_flatten.elf ^
      -scriptPath scripts -postScript ghidra_export.java gcd.ghidra.c gcd
  ```

## 5. Vositani ishlatish

### 5.1. Web UI (eng qulay)
```bat
deobf web
```
Brauzerda <http://127.0.0.1:5000> ni oching:
1. psevdokodni joylang yoki **"Namuna yuklash"** dan birini tanlang;
2. dvigatelni tanlang: **Haiku** (standart, arzon) / Sonnet / Opus / Offline;
3. **"Tahlil qilish"** tugmasini bosing;
4. natijani ko'ring va kerak bo'lsa **Markdown/HTML/JSON** qilib yuklab oling.

### 5.2. Buyruq qatori (CLI)
```bat
deobf functions gcd.ida.c                         :: fayldagi funksiyalar ro'yxati
deobf analyze gcd.ida.c                           :: Claude Haiku bilan tahlil (standart)
deobf analyze gcd.ida.c --model sonnet            :: kuchliroq model
deobf analyze gcd.ida.c --model opus              :: eng kuchli model
deobf analyze gcd.ida.c --offline                 :: bepul, LLM'siz
deobf analyze kod.c -f sub_401136                 :: faqat bitta funksiya
deobf analyze kod.c --format html -o natija.html  :: HTML hisobot
deobf analyze kod.c --lang ru                     :: tushuntirishlar rus tilida
```

Foydali parametrlar:

| Parametr | Ma'nosi | Standart |
|---|---|---|
| `--model` | `haiku` / `sonnet` / `opus` yoki to'liq model nomi | `haiku` |
| `--effort` | o'ylash chuqurligi: `low` (arzon) / `medium` / `high` | `medium` |
| `--max-rounds` | tekshiruvdan o'tmasa, necha marta tuzatish so'raladi | `3` |
| `--tests` | differensial testlar soni | `2000` |
| `--no-cache` | keshni chetlab o'tib, qaytadan so'rash | — |

Standart modelni doimiy o'zgartirish: `.env` fayliga `DEOBF_MODEL=sonnet` qo'shing.

### 5.3. Baholash (namunalar bo'yicha)
```bat
deobf eval --offline -o docs\baholash_offline.md        :: bepul
deobf eval --model haiku -o docs\baholash_haiku.md      :: Claude Haiku (5 namuna ≈ $0.01)
deobf eval --model sonnet -o docs\baholash_sonnet.md    :: taqqoslash uchun
```
IDA psevdokodi bilan baholash: namunalarni (`samples/bin/*.elf`) IDA'da ochib, har birini
`samples/decompiled/<id>.ida.c` nomi bilan saqlang (masalan, `s1_mba.ida.c`), so'ng:
```bat
deobf eval --model haiku --source ida -o docs\baholash_haiku_ida.md
```

## 6. Natijani qanday o'qish kerak

| Belgi | Ma'nosi |
|---|---|
| ✅ **Tasdiqlandi** | kod kompilyatsiya bo'ldi va asl psevdokod bilan minglab testda bir xil natija berdi |
| 🟡 **Kompilyatsiya bo'ldi** | kod to'g'ri yozilgan, lekin avtomatik solishtirib bo'lmadi (ko'rsatkichlar, tashqi funksiyalar). Qo'lda ko'zdan kechiring |
| ❌ **Farq qiladi / xato** | barcha urinishlardan keyin ham natija tekshiruvdan o'tmadi. `--model sonnet` bilan qayta urinib ko'ring |

- **Qatorlar** va **tsiklomatik murakkablik** qanchalik kamaysa, kod shunchalik soddalashgan.
- **Statik tahlil topilmalari** — LLM'siz, matematik isbotlangan faktlar.
- **Ishonch** — modelning o'z bahosi. Rasmiy tekshiruv natijasi esa yuqoridagi belgi.

## 7. Pul tejash bo'yicha maslahatlar
1. Avval `--offline` bilan ko'ring — ko'p narsa bepul aniqlanadi.
2. Standart **Haiku** modeli ko'p holatlar uchun yetarli. Faqat qiyin holatlarda `--model sonnet/opus` ishlating.
3. `--effort low` — yanada arzon.
4. Bir xil kodni qayta tahlil qilish **bepul** (disk kesh, `.deobf_cache/` papkasi).
5. Butun dasturni emas, kerakli funksiyani tahlil qiling (`-f nomi`).

## 8. Muammolar va yechimlar

| Muammo | Yechim |
|---|---|
| `deobf` buyrug'i topilmadi | virtual muhitni faollashtiring: `.venv\Scripts\activate` |
| "API kalit noto'g'ri yoki yo'q" | `.env` faylini tekshiring (loyiha papkasida bo'lishi kerak) |
| "C kompilyatori topilmadi" | gcc o'rnating (1-bo'lim) yoki `DEOBF_CC` muhit o'zgaruvchisida kompilyator yo'lini ko'rsating |
| "Bog'lash (link) bo'lmadi" | psevdokod boshqa funksiyalarni chaqiradi yoki global ma'lumot yo'q — ularni ham kiriting (Shift+E) |
| "Model so'rovni bajarishdan bosh tortdi" | `--model sonnet` bilan urinib ko'ring; natija baribir offline rejimdan beriladi |
| Terminalda harflar buziladi | `chcp 65001` buyrug'ini bering (UTF-8) |
