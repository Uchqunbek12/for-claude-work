# 04. Internetga chiqarish (deploy)

Bu yo'riqnoma vositani internetga — havola orqali ochiladigan manzilga — qanday qo'yishni tushuntiradi.

> **Qisqasi.** Siz uchun mo'ljallangan variant — **yopiq rejim**: saytga faqat **kirish kodi** bilan kiriladi; kirganlar
> uchun Claude **sizning API kalitingiz** bilan ishlaydi (kunlik byudjet chegarasi bilan) va kod **to'liq tekshiriladi**
> (gcc + differensial test). Ya'ni loyiha to'liq ishlaydi, lekin kodni bilmagan odam hech narsa qila olmaydi.
> Ustoz va o'zingiz kodni ishlatasiz.

---

## 1. Uch rejim

| | Shaxsiy (kompyuteringizda) | Ochiq rejim (kodsiz, hamma uchun) | **Yopiq rejim** (kod bilan) |
|---|---|---|---|
| Yoqilishi | `deobf web` | `DEOBF_PUBLIC=1` | `DEOBF_PUBLIC=1` + `DEOBF_ACCESS_CODE=<kod>`; server kaliti va to'liq tekshiruv **avtomatik** yoqiladi (kalit `ANTHROPIC_API_KEY` bo'lsa) |
| Kim kiradi | faqat siz | hamma | kodni biladiganlar |
| API kalit | `.env` dagi sizniki | serverda yo'q; har kim o'zinikini kiritadi | **serverdagi sizning kalitingiz** (`ANTHROPIC_API_KEY`) yoki o'zinikini kiritish |
| Kod ishga tushiriladimi (to'liq tekshiruv) | ha | **yo'q** → «Tekshirilmadi» | **ha**, alohida huquqsiz foydalanuvchi nomidan (ajratish ishlasa) |
| Cheklovlar | yumshoq | qattiq | qattiq + kunlik Claude byudjeti |

**Nega «ochiq rejim»da «Tekshirilmadi» chiqadi, yopiq rejimda esa yo'q?** Tekshiruv kodni *ishga tushiradi*. Kodni hamma
yuborishi mumkin bo'lsa, begona odam zararli kod yuborishi mumkin — shuning uchun ochiq rejimda ishga tushirilmaydi.
Yopiq rejimda kodni faqat parolni bilganlar yuboradi, shuning uchun to'liq tekshiruvni yoqish mumkin.

---

## 2. Xavfsizlik: yopiq rejimda nimalar himoya qiladi

Yopiq rejim **kirish kodi**, **server kaliti** va **kodni ishga tushirish**ni birlashtiradi. Agar kimdir kirish kodini
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

**Servisni qo'lda yaratgan bo'lsangiz** (Blueprint o'rniga «New → Web Service»): Environment bo'limiga **ikkita** maydon yozish yetadi:
`DEOBF_ACCESS_CODE` (kirish kodi) va `ANTHROPIC_API_KEY` (kalit). Qolganlari (`DEOBF_PUBLIC`, `DEOBF_TRUSTED_PROXIES`,
`DEOBF_SANDBOX_UID`) Dockerfile'da berilgan, server kaliti va to'liq tekshiruv esa kirish kodi bor bo'lgani uchun o'zi yoqiladi.
O'zgartirgandan keyin Render servisni qayta ishga tushiradi (yoki **Manual Deploy → Deploy latest commit**).

### 3.3. Nima uchun aynan shunday

| Tanlov | Sabab |
|---|---|
| Docker | Qayerda ochilsa ham bir xil ishlaydi. |
| Server `root`, kod `sandbox` (uid 10002) nomidan | Serverning kaliti va xotirasini tekshirilayotgan kod o'qiy olmasligi uchun (haqiqiy foydalanuvchi ajratish). |
| `--workers 1 --threads 8` | Hisobotlar va cheklovlar jarayon xotirasida; ko'p jarayonda yuklab olish havolasi tasodifiy «topilmadi» bo'lardi. |
| `/healthz` (kirishsiz) | Render sog'liq tekshiruvi kodsiz ham ishlashi uchun. |
| `DEOBF_TRUSTED_PROXIES=1` | Render proksi orqasida; shunda urinish cheklovi har bir haqiqiy mijoz IP'si uchun. To'g'ridan-to'g'ri internetga ochilsa o'rnatilmaydi. |
| `DEOBF_SESSION_SECRET` (Render o'zi yaratadi) | Sessiya cookie imzosi. |

### 3.3.1. Sayt nomi va havola

* **Sahifadagi nom** (sarlavha va tepada): Render → Environment → `DEOBF_SITE_NAME` (masalan, `Kod Ochar`). Bo'sh bo'lsa `deobfuskatsiya`.
* **Havola nomi** (`https://<nom>.onrender.com`): Render → servis → **Settings → Name**. Havola shu nomdan olinadi; band bo'lmasa o'zgaradi.

### 3.3.2. Muammolar

| Belgi | Sabab va yechim |
|---|---|
| Sayt kod so'ramaydi, «Sayt hali yopilmagan: kirish kodi qo'yilmagan» chiqadi (503) | `ANTHROPIC_API_KEY` bor, lekin `DEOBF_ACCESS_CODE` yo'q. Kodsiz sayt hammaga ochiq bo'lardi, shuning uchun u to'xtatiladi va kalit ishlatilmaydi. Render → Environment → `DEOBF_ACCESS_CODE` = o'zingiz tanlagan kod → Save. |
| Kirgandan keyin qizil blok «Serverda Claude kaliti ulanmagan» va «Sizning kalitingiz» maydoni chiqadi | Render → Environment da `ANTHROPIC_API_KEY` yo'q, bo'sh yoki nomi boshqacha yozilgan (sahifa o'xshash nomlarni o'zi ko'rsatadi). To'g'ri nom: `ANTHROPIC_API_KEY`. Saqlagach Render servisni o'zi qayta ishga tushiradi. |
| Kalit maydoni yo'q, lekin pastda qizil «Kalit noto'g'ri yoki bekor qilingan» | Kalit Render'ga ulangan, lekin Anthropic uni qabul qilmayapti: console.anthropic.com da kalit o'chirilgan/bekor qilingan yoki to'liq nusxalanmagan. Yangi kalit yarating va `ANTHROPIC_API_KEY` qiymatini almashtiring. |
| «Server kodni ishga tushirmaydi… Tekshirilmadi» | Render konteynerda kodni alohida foydalanuvchi nomidan ishga tushirishga ruxsat bermadi (log'da «OGOHLANTIRISH» bor). Claude va Offline ishlayveradi, faqat gcc + test o'chadi. |
| Kod yozilganda ham kirmaydi / «Juda ko'p noto'g'ri urinish» | Noto'g'ri urinishlar cheklovi (IP: 15 daqiqada 5 ta). Biroz kuting. |
| Servis ishga tushmaydi, log'da `DEOBF_USE_SERVER_KEY ... DEOBF_ACCESS_CODE` | `DEOBF_USE_SERVER_KEY=1` yozilgan, lekin `DEOBF_ACCESS_CODE` bo'sh. Kodni yozing (yoki `DEOBF_USE_SERVER_KEY` ni olib tashlang). |

### 3.4. Hali sinalmaganlar (halol)

* `docker build` bu kompyuterda ishga tushirilmagan (Docker yo'q). Dockerfile'dagi barcha qadamlar (o'rnatish, gunicorn,
  foydalanuvchi ajratish, kirish kodi, to'liq tekshiruv) shu Linux muhitida **xuddi shu sozlamalar bilan** qayta ishlab
  ko'rilgan va ishlagan.
* Render ustidagi haqiqiy ishga tushirishni faqat siz qila olasiz: unda hisobingiz kerak.
* Claude haqiqiy kalit bilan lokal sinaldi (5 funksiya, `docs/baholash_claude_sonnet.md`); Render ustida esa Claude hali ishlatilmagan.

---

## 4. Ochiq rejim (kodsiz, hamma uchun)

Agar havolani kodsiz tarqatmoqchi bo'lsangiz: `DEOBF_ACCESS_CODE`, `DEOBF_USE_SERVER_KEY`, `DEOBF_NATIVE` ni **qo'ymang**. Shunda:
server kalit saqlamaydi (foydalanuvchi o'zinikini kiritadi), kod ishga tushirilmaydi («Tekshirilmadi»), cheklovlar qattiq
(≤ 20 000 belgi, ≤ 3 funksiya, 90 s, 10 daqiqada 15 tahlil).

---

## 5. O'zingiz sinab ko'rish

Kompyuteringizda ochiq rejim ko'rinishini: `deobf web --public`.

Yopiq rejimni kompyuteringizda sinash (Linux/macOS, root bo'lsangiz ajratish ham ishlaydi):

```bash
DEOBF_PUBLIC=1 DEOBF_ACCESS_CODE=1234 DEOBF_NATIVE=1 DEOBF_USE_SERVER_KEY=1 \
ANTHROPIC_API_KEY=sk-ant-... deobf web
```
Root bo'lmasangiz, `DEOBF_USE_SERVER_KEY` bilan birga kod ishga tushirilmaydi (ajratish sinovi o'tmaydi) — bu kutilgan,
xavfsiz xatti-harakat.

Docker bilan: `docker build -t deobf-agent .` va `docker run -p 8000:8000 -e DEOBF_PUBLIC=1 deobf-agent`.

---

## 6. Boshqa xostinglar

`Dockerfile` oddiy, shuning uchun Docker qabul qiladigan har qanday xostingda ishlaydi. Yopiq rejim uchun xosting
konteynerni **root** sifatida ishga tushirishga ruxsat berishi kerak (foydalanuvchi ajratish uchun); bo'lmasa kod ishga
tushirilmaydi va natija «Tekshirilmadi» bo'ladi.

```bash
pip install -e ".[deploy]"      # gunicorn o'rnatadi
DEOBF_PUBLIC=1 gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 8 --timeout 120 wsgi:app
```
