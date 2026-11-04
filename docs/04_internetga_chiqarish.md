# 04. Internetga chiqarish (deploy)

Bu yo'riqnoma vositani internetga — havola orqali ochiladigan manzilga — qanday qo'yishni tushuntiradi.

> **Qisqasi.** Siz uchun mo'ljallangan variant — **yopiq demo**: saytga faqat **kirish kodi** bilan kiriladi; kirganlar
> uchun Claude **sizning API kalitingiz** bilan ishlaydi (kunlik byudjet chegarasi bilan) va kod **to'liq tekshiriladi**
> (gcc + differensial test). Ya'ni loyiha to'liq ishlaydi, lekin kodni bilmagan odam hech narsa qila olmaydi.
> Ustoz va o'zingiz kodni ishlatasiz.

---

## 1. Uch rejim

| | Shaxsiy (kompyuteringizda) | Ochiq demo (kodsiz, hamma uchun) | **Yopiq demo** (kod bilan) |
|---|---|---|---|
| Yoqilishi | `deobf web` | `DEOBF_PUBLIC=1` | `DEOBF_PUBLIC=1` + `DEOBF_ACCESS_CODE=<kod>` |
| Kim kiradi | faqat siz | hamma | kodni biladiganlar |
| API kalit | `.env` dagi sizniki | serverda yo'q; har kim o'zinikini kiritadi | **serverdagi sizning kalitingiz** (`DEOBF_USE_SERVER_KEY=1`) yoki o'zinikini kiritish |
| Kod ishga tushiriladimi (to'liq tekshiruv) | ha | **yo'q** → «Tekshirilmadi» | **ha** (`DEOBF_NATIVE=1`), alohida huquqsiz foydalanuvchi nomidan |
| Cheklovlar | yumshoq | qattiq | qattiq + kunlik Claude byudjeti |

**Nega «ochiq demo»da «Tekshirilmadi» chiqadi, yopiq demoda esa yo'q?** Tekshiruv kodni *ishga tushiradi*. Kodni hamma
yuborishi mumkin bo'lsa, begona odam zararli kod yuborishi mumkin — shuning uchun ochiq demoda ishga tushirilmaydi.
Yopiq demoda kodni faqat parolni bilganlar yuboradi, shuning uchun to'liq tekshiruvni yoqish mumkin.

---

## 2. Xavfsizlik: yopiq demoda nimalar himoya qiladi

Yopiq demo **kirish kodi**, **server kaliti** va **kodni ishga tushirish**ni birlashtiradi. Agar kimdir kirish kodini
topsa, u bularning hammasiga qo'l uzatadi. Shuning uchun qatlamlar:

| Xavf | Himoya |
|---|---|
| Kodni taxmin qilish (4 xonali kod = 10 000 variant) | Noto'g'ri urinishlar **cheklangan**: bitta IP'dan 15 daqiqada 5 ta; barcha IP'lardan jami 1 soatda 40 ta — undan keyin hamma bloklanadi (to'g'ri kod ham, to'xtaguncha). Kod taqqoslash vaqt bo'yicha sezgir emas (`hmac.compare_digest`). |
| Kod topilsa, Claude pulini sarflash | **Kunlik byudjet** (`DEOBF_DAILY_BUDGET_USD`, standart $2): shundan keyin Claude to'xtaydi, offline ishlayveradi. Anthropic konsolida oylik **spend limit** qo'ying (3-bo'lim). |
| Kod topilsa, serverdagi kalitni o'g'irlash | Tekshirilayotgan kod **alohida huquqsiz foydalanuvchi** (`DEOBF_SANDBOX_UID`) nomidan ishlaydi: u serverning muhit o'zgaruvchilarini (`/proc/<pid>/environ`, ya'ni kalit) va xotirasini o'qiy olmaydi (`Permission denied`; bu testda tekshirilgan). Server ishga tushganda shu ajratish **o'zi sinab ko'riladi**; sinov o'tmasa, kod ishga tushirilmaydi. |
| Kalitni kodsiz ishlatish | `DEOBF_USE_SERVER_KEY` kirish kodisiz **ishga tushmaydi** (server boot xatosi beradi). `DEOBF_NATIVE` ham kirish kodisiz ishlamaydi. |
| Kirish kodi/kalit GitHub'da ko'rinib qolishi | Ikkalasi `render.yaml` da **yo'q**: u yerda faqat `sync: false` belgisi bor, qiymatni Render sizdan so'raydi va faqat o'z sozlamalarida saqlaydi. |
| Sessiyani o'g'irlash | Cookie `HttpOnly`, `SameSite=Lax`, HTTPS'da `Secure`; 12 soatdan keyin tugaydi; kirishdan keyingi sahifalar keshlanmaydi. |
| Boshqa saytdan so'rov (CSRF) | `Origin`/`Sec-Fetch-Site` tekshiruvi. |
| Xato tuzilmalar | Qat'iy CSP (skriptlar faqat o'zimizdan), matn doim ekranlanadi. |

> **Halol ogohlantirish.** 4 xonali kod — **kuchsiz** parol. Yuqoridagi cheklovlar uni *taxmin qilib topishni* juda
> sekinlashtiradi (umumiy chegara soatiga 40 urinish: o'rtacha ~5 kun, eng ko'pi bilan ~10 kun, shu paytda sayt sizga ham
> vaqtincha yopiladi), lekin imkonsiz qilmaydi. Shuning uchun byudjet chegarasi va ajratilgan
> foydalanuvchi bor. Ustozga ko'rsatib bo'lgach, kodni **o'zgartirib qo'ying** (Render → Environment →
> `DEOBF_ACCESS_CODE`) yoki xizmatni to'xtating. Kod uzunroq/murakkabroq bo'lsa, xavf yanada kamayadi.

---

## 3. Joylash: Render.com (bepul, Docker)

Repozitoriyadagi `Dockerfile` va `render.yaml` tayyor. GitHub'da asosiy (default) branch `claude/vibrant-heisenberg-teie45`
(alohida `main` yo'q) — Render uni o'zi oladi.

### 3.1. Oldindan: Anthropic'da kalit va limit

1. [console.anthropic.com](https://console.anthropic.com) → **API keys** → yangi kalit yarating (`sk-ant-...`). Uni **hech kimga
   yubormang** va chatga yozmang.
2. **Billing** → balansni to'ldiring (kichik summa yetadi).
3. **Limits** (yoki Billing sozlamalari) → **oylik xarajat chegarasi** qo'ying (masalan, $5–10). Bu eng ishonchli himoya:
   kod qo'lga tushsa ham, siz belgilagan summadan ortiq sarflanmaydi.

### 3.2. Render'da

1. [render.com](https://render.com) ga **GitHub bilan** kiring.
2. **New → Blueprint** → repozitoriya `Uchqunbek12/for-claude-work` ni tanlang (Render GitHub'ga kirishga ruxsat so'raydi).
   *(Tugma nomlari vaqt o'tishi bilan o'zgarishi mumkin: maqsad — repozitoriyani ulab, `render.yaml` dan servis yaratish.)*
3. Render `render.yaml` ni o'qiydi va **ikki qiymatni so'raydi**:
   * `DEOBF_ACCESS_CODE` — saytga kirish kodi (o'zingiz tanlagan 4 xonali son);
   * `ANTHROPIC_API_KEY` — 3.1-qadamdagi kalit.
4. **Apply / Create** bosing. Qurilish 3–6 daqiqa davom etadi (gcc o'rnatiladi).
5. Tayyor bo'lgach, Render `https://deobf-agent-xxxx.onrender.com` havolasini beradi. Ochganda **kirish kodi** so'raladi.
6. Namoyishdan oldin sahifani bir marta oching: bepul reja 15 daqiqa foydalanilmasa «uxlab qoladi» va birinchi
   ochilish 30–60 soniya sekinroq bo'ladi.

### 3.3. Nima uchun aynan shunday

| Tanlov | Sabab |
|---|---|
| Docker | Qayerda ochilsa ham bir xil ishlaydi. |
| Server `root`, kod `sandbox` (uid 10002) nomidan | Serverning kaliti va xotirasini tekshirilayotgan kod o'qiy olmasligi uchun (haqiqiy foydalanuvchi ajratish). |
| `--workers 1 --threads 8` | Hisobotlar va cheklovlar jarayon xotirasida; ko'p jarayonda yuklab olish havolasi tasodifiy «topilmadi» bo'lardi. |
| `/healthz` (kirishsiz) | Render sog'liq tekshiruvi kodsiz ham ishlashi uchun. |
| `DEOBF_TRUSTED_PROXIES=1` | Render proksi orqasida; shunda urinish cheklovi har bir haqiqiy mijoz IP'si uchun. To'g'ridan-to'g'ri internetga ochilsa o'rnatilmaydi. |
| `DEOBF_SESSION_SECRET` (Render o'zi yaratadi) | Sessiya cookie imzosi. |

### 3.4. Hali sinalmaganlar (halol)

* `docker build` bu kompyuterda ishga tushirilmagan (Docker yo'q). Dockerfile'dagi barcha qadamlar (o'rnatish, gunicorn,
  foydalanuvchi ajratish, kirish kodi, to'liq tekshiruv) shu Linux muhitida **xuddi shu sozlamalar bilan** qayta ishlab
  ko'rilgan va ishlagan.
* Render ustidagi haqiqiy ishga tushirishni faqat siz qila olasiz: unda hisobingiz kerak.
* Claude'ning haqiqiy javobi (matn sifati, narx) haqiqiy kalit bilan hali ko'rilmagan.

---

## 4. Ochiq demo (kodsiz, hamma uchun)

Agar havolani kodsiz tarqatmoqchi bo'lsangiz: `DEOBF_ACCESS_CODE`, `DEOBF_USE_SERVER_KEY`, `DEOBF_NATIVE` ni **qo'ymang**. Shunda:
server kalit saqlamaydi (foydalanuvchi o'zinikini kiritadi), kod ishga tushirilmaydi («Tekshirilmadi»), cheklovlar qattiq
(≤ 20 000 belgi, ≤ 3 funksiya, 90 s, 10 daqiqada 15 tahlil).

---

## 5. O'zingiz sinab ko'rish

Kompyuteringizda ochiq demo ko'rinishini: `deobf web --public`.

Yopiq demoni kompyuteringizda sinash (Linux/macOS, root bo'lsangiz ajratish ham ishlaydi):

```bash
DEOBF_PUBLIC=1 DEOBF_ACCESS_CODE=1234 DEOBF_NATIVE=1 DEOBF_USE_SERVER_KEY=1 \
ANTHROPIC_API_KEY=sk-ant-... deobf web
```
Root bo'lmasangiz, `DEOBF_USE_SERVER_KEY` bilan birga kod ishga tushirilmaydi (ajratish sinovi o'tmaydi) — bu kutilgan,
xavfsiz xatti-harakat.

Docker bilan: `docker build -t deobf-agent .` va `docker run -p 8000:8000 -e DEOBF_PUBLIC=1 deobf-agent`.

---

## 6. Boshqa xostinglar

`Dockerfile` oddiy, shuning uchun Docker qabul qiladigan har qanday xostingda ishlaydi. Yopiq demo uchun xosting
konteynerni **root** sifatida ishga tushirishga ruxsat berishi kerak (foydalanuvchi ajratish uchun); bo'lmasa kod ishga
tushirilmaydi va natija «Tekshirilmadi» bo'ladi.

```bash
pip install -e ".[deploy]"      # gunicorn o'rnatadi
DEOBF_PUBLIC=1 gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 8 --timeout 120 wsgi:app
```
