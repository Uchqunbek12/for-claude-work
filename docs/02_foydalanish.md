# 02. Foydalanish yo'riqnomasi (qadam-baqadam)

Bu yo'riqnoma Windows uchun yozilgan. Linux/macOS'da buyruqlar deyarli bir xil:
`.venv\Scripts\activate` o'rniga `source .venv/bin/activate` ishlatiladi.

---

## 0. ENG OSON YO'L (Windows): 4 ta faylni ikki marta bosish

Loyiha papkasida 4 ta `.bat` fayl bor. Ularni **tartib bilan, sichqoncha bilan ikki marta bosib** ishga tushiring:

| Fayl | Nima qiladi | Qachon |
|---|---|---|
| `1_ornatish.bat` | virtual muhit yaratadi va kutubxonalarni o'rnatadi | **bir marta** |
| `2_kalit_kiritish.bat` | API kalitni so'raydi, `.env` faylini **to'g'ri formatda** yaratadi va kalitni darhol tekshiradi | **bir marta** (kalit o'zgarsa — qayta) |
| `3_web_ishga_tushirish.bat` | Web UI'ni ishga tushiradi va brauzerni o'zi ochadi | **har safar** ishlatganda |
| `4_tekshirish.bat` | diagnostika: Python, kutubxonalar, `.env`, kalit, gcc — nima ishlayotganini ko'rsatadi | muammo bo'lsa |

> Bu fayllar `.venv` ni "faollashtirish" talab qilmaydi va PowerShell ruxsatlari bilan bog'liq muammolarni chetlab o'tadi.

### Web UI ishlashi uchun eng muhim qoida
`3_web_ishga_tushirish.bat` qora oyna (terminal) ochadi va unda quyidagi yozuv chiqadi:
```
============================================================
  Web UI ishga tushdi:  http://127.0.0.1:5000
  Brauzerda shu manzilni oching (avtomatik ochilishi kerak).
  DIQQAT: bu oynani YOPMANG — yopsangiz Web UI to'xtaydi.
============================================================
```
- Bu qora oyna — **serverning o'zi**. U ochiq turgan paytdagina Web UI ishlaydi. Oynani kichraytirib qo'yish mumkin, lekin **yopmang**.
- Brauzer o'zi ochilmasa, Chrome/Edge'ning manzil satriga qo'lda **`http://127.0.0.1:5000`** deb yozing.
- Ishni tugatgach, qora oynani yoping yoki unda `Ctrl+C` bosing.

### Kalit ishlayaptimi?
`2_kalit_kiritish.bat` yoki `4_tekshirish.bat` oxirida shunday qator chiqadi:
```
✅ Model 'haiku': Kalit ishlayapti ✅ — model mavjud: Claude Haiku 5.5 (claude-haiku-5-5)
```
Bu tekshiruv **bepul**, chunki Claude hech qanday matn yaratmaydi, server faqat kalitni tasdiqlaydi.
Web UI'da ham shunday tekshiruv bor: **"Kalitni tekshirish"** tugmasi.

Agar ❌ chiqsa, uning yonida sababi yoziladi:

| Xabar | Ma'nosi | Nima qilish kerak |
|---|---|---|
| `ANTHROPIC_API_KEY topilmadi` | `.env` fayli yo'q yoki boshqa papkada | `2_kalit_kiritish.bat` ni qayta ishga tushiring |
| `Kalit noto'g'ri yoki bekor qilingan` | kalit noto'liq nusxalangan yoki o'chirilgan | console.anthropic.com → API Keys → yangi kalit yarating |
| `Kalitga ruxsat yo'q` / balans bilan bog'liq xabar | hisobda mablag' yo'q | console.anthropic.com → Billing |
| `Claude serveriga ulanib bo'lmadi` | internet yoki proksi muammosi | internet aloqasini tekshiring |

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
4. **`2_kalit_kiritish.bat`** ni ishga tushiring va kalitni joylang. Fayl `.env` ni o'zi yaratadi
   va kalitni tekshiradi.

   Qo'lda qilmoqchi bo'lsangiz, loyiha papkasida `.env` nomli fayl yarating (Notepad → *Save as* →
   "Save as type: **All files**" → nom: `.env`) va unga bitta qator yozing:
   ```
   ANTHROPIC_API_KEY=sk-ant-...sizning-kalitingiz...
   ```
   Vosita `.env` ni har qanday kodlashda (UTF-8, UTF-16) o'qiydi, `.env.txt` nomini ham qabul qiladi.
5. Tekshiring: `4_tekshirish.bat` yoki `deobf check`.

> ⚠️ `.env` fayli `.gitignore` da, ya'ni GitHub'ga yuklanmaydi. Kalitni hech qachon kod ichiga
> yozmang va hech kimga yubormang (menga ham).

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
Ishga tushirish — ikki usuldan biri:
- `3_web_ishga_tushirish.bat` ni ikki marta bosing (**tavsiya**), yoki
- terminalda: `.venv\Scripts\python -m deobf_agent web` (yoki `.venv` faol bo'lsa `deobf web`).

Brauzer o'zi ochiladi (ochilmasa, <http://127.0.0.1:5000> ni yozing). Qora oynani yopmang.

Sahifada:
1. psevdokodni joylang (IDA: F5 → Ctrl+A → Ctrl+C → shu yerga Ctrl+V), faylni tanlang
   yoki **"Namuna yuklash"** ro'yxatidan birini tanlang;
2. **"Model (dvigatel)"** ro'yxatidan modelni tanlang (5.4-bo'lim);
3. birinchi marta **"Kalitni tekshirish"** tugmasini bosing — "Kalit ishlayapti ✅" chiqishi kerak;
4. **"Tahlil qilish"** tugmasini bosing. Claude bilan 10–60 soniya davom etadi;
5. natijani ko'ring: tepada ✅/🟡/❌ belgisi, asl va toza kod yonma-yon, pastda bloklar bo'yicha tushuntirish;
6. kerak bo'lsa **Markdown / HTML / JSON** qilib yuklab oling.

### 5.2. Buyruq qatori (CLI)
> Buyruqlar ishlashi uchun avval terminalda `.venv\Scripts\activate` bajaring (cmd'da).
> PowerShell "running scripts is disabled" xatosini bersa: `deobf` o'rniga
> `.venv\Scripts\python -m deobf_agent` deb yozing (masalan, `.venv\Scripts\python -m deobf_agent check`).

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

### 5.3. Model tanlash va "model qo'shish"
Modellarni **qo'shish shart emas** — uchta Claude modeli vositaga allaqachon kiritilgan. Siz faqat
qaysi birini ishlatishni **tanlaysiz**:

| Model | Qisqa nomi | Narx (1 funksiya) | Qachon ishlatish |
|---|---|---|---|
| Claude Haiku 5.5 | `haiku` | ~$0.001 | **standart** — ko'p holatlar uchun yetarli |
| Claude Sonnet 5.5 | `sonnet` | ~$0.03 | Haiku natijasi ❌ yoki 🟡 bo'lsa |
| Claude Opus 5.5 | `opus` | ~$0.05 | eng murakkab funksiyalar uchun |
| Offline | `--offline` | $0 | API kalitsiz, faqat statik tahlil |

Tanlash usullari:
- **Web UI:** "Model (dvigatel)" ro'yxatidan tanlang. Ro'yxatda bo'lmagan boshqa Claude modelini
  ishlatish uchun **"Boshqa model"** ni tanlang va to'liq nomini yozing (masalan, `claude-sonnet-5-5`).
  Mana shu "model qo'shish" bo'ladi. Ishlashini **"Kalitni tekshirish"** tugmasi bilan tekshiring.
- **CLI:** `deobf analyze kod.c --model sonnet` (yoki to'liq nom: `--model claude-sonnet-5-5`).
- **Doimiy standart:** `.env` fayliga ikkinchi qator qo'shing: `DEOBF_MODEL=sonnet`.
  Shundan keyin `--model` yozilmasa, Sonnet ishlatiladi.

> Model nomlari kodda bitta joyda — `deobf_agent/llm.py` faylidagi `MODEL_ALIASES` lug'atida.
> Kelajakda yangi model chiqsa, uni shu yerga bitta qator qilib qo'shish kifoya
> (`"yangi": "claude-yangi-model-nomi",`). Narxi esa `PRICES` lug'atiga qo'shiladi.

### 5.4. Baholash (namunalar bo'yicha)
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

### 5.5. Internetga chiqarish (demo rejimi)
Vositani boshqalar ham ishlata oladigan qilib internetga qo'yish mumkin. Buning uchun **public rejim**
bor: server kalit saqlamaydi, cheklovlar qattiq. Avval o'z kompyuteringizda sinab ko'ring:
```bat
deobf web --public
```
To'liq yo'riqnoma (Render.com, Docker, xavfsizlik): **[docs/04_internetga_chiqarish.md](04_internetga_chiqarish.md)**.

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
| `deobf` buyrug'i topilmadi | `.bat` fayllardan foydalaning yoki `.venv\Scripts\python -m deobf_agent ...` deb yozing |
| Web UI ochilmaydi, qora oyna darhol yopiladi | `3_web_ishga_tushirish.bat` endi xato matnini ko'rsatib to'xtaydi — matnni nusxalab yuboring. Oldin `1_ornatish.bat` bajarilganini tekshiring |
| "port band" xatosi | Web UI allaqachon ochiq (boshqa qora oynada) yoki 5000-portni boshqa dastur ishlatyapti: `.venv\Scripts\python -m deobf_agent web --port 5050` |
| Brauzerda "Saytga ulanib bo'lmadi" | qora oyna yopilgan — `3_web_ishga_tushirish.bat` ni qayta ishga tushiring |
| `.ps1 cannot be loaded ... running scripts is disabled` | PowerShell cheklovi: `.bat` fayllardan yoki `cmd` dan foydalaning |
| "API kalit noto'g'ri yoki yo'q" | `4_tekshirish.bat` ni ishga tushiring — u `.env` qayerdan qidirilganini va kalitning boshi/oxirini ko'rsatadi |
| "C kompilyatori topilmadi" | gcc o'rnating (1-bo'lim) yoki `DEOBF_CC` muhit o'zgaruvchisida kompilyator yo'lini ko'rsating |
| "Bog'lash (link) bo'lmadi" | psevdokod boshqa funksiyalarni chaqiradi yoki global ma'lumot yo'q — ularni ham kiriting (Shift+E) |
| "Model so'rovni bajarishdan bosh tortdi" | `--model sonnet` bilan urinib ko'ring; natija baribir offline rejimdan beriladi |
| Terminalda harflar buziladi | `chcp 65001` buyrug'ini bering (UTF-8) |
