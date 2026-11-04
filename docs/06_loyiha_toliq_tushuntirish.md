# 06. Loyiha to'liq tushuntirish — 0 dan oxirigacha

> **Bu hujjat kim uchun.** Siz (talaba) ustozingizga loyihani ko'rsatishingiz va **har bir qarorni himoya qila olishingiz**
> kerak. Shuning uchun bu yerda faqat "nima qildik" emas, balki har bir narsa uchun **"nima bu?"**, **"nega kerak?"** va
> **"qaysi faylning vazifasi?"** degan savollarga javob berilgan. Bir narsani tushunmasangiz — pastdagi 2-bo'limdagi
> lug'atdan qidiring.
>
> **Mavzu:** 10. *Obfuskatsiyalangan kodni deobfuskatsiya qilish agenti.* IDA Pro yoki Ghidra orqali olingan
> obfuskatsiyalangan kodni LLM yordamida soddalashtiradigan, C tilidagi ekvivalentini yaratadigan va har bir blokni inson
> tushunadigan tilda tushuntiradigan vosita ishlab chiqish.

---

## Mundarija

1. [Qisqa xulosa (1 sahifa)](#1-qisqa-xulosa)
2. [Lug'at: har bir atama nima va nega kerak](#2-lugat-har-bir-atama-nima-va-nega-kerak)
3. [Topshiriq nima edi va biz uni qanday hal qildik](#3-topshiriq-nima-edi-va-biz-uni-qanday-hal-qildik)
4. [Umumiy sxema: ma'lumot qanday oqadi](#4-umumiy-sxema-malumot-qanday-oqadi)
5. [Fayllar va ularning vazifalari](#5-fayllar-va-ularning-vazifalari)
6. [Har bir qism qanday ishlaydi (chuqur)](#6-har-bir-qism-qanday-ishlaydi-chuqur)
7. [Bosqichma-bosqich: nima qildik va nega](#7-bosqichma-bosqich-nima-qildik-va-nega)
8. [Ishlatilgan vositalar](#8-ishlatilgan-vositalar)
9. [Xatolar va saboqlar (halol hisobot)](#9-xatolar-va-saboqlar-halol-hisobot)
10. [Natijalar va ularni qanday o'qish kerak](#10-natijalar-va-ularni-qanday-oqish-kerak)
11. [Xavfsizlik: har bir himoya nima uchun](#11-xavfsizlik-har-bir-himoya-nima-uchun)
12. [Internetga chiqarish](#12-internetga-chiqarish)
13. [API ishlayaptimi? Kalit haqida](#13-api-ishlayaptimi-kalit-haqida)
14. [Cheklovlar: nima ishlamaydi](#14-cheklovlar-nima-ishlamaydi)
15. [Ustozga namoyish rejasi (5–7 daqiqa)](#15-ustozga-namoyish-rejasi-57-daqiqa)
16. [Ustoz berishi mumkin bo'lgan savollar va javoblar](#16-ustoz-berishi-mumkin-bolgan-savollar-va-javoblar)
17. [Nazariy qism uchun nima qoldi](#17-nazariy-qism-uchun-nima-qoldi)

---

## 1. Qisqa xulosa

**Muammo.** Ba'zi dasturlar *ataylab* tushunib bo'lmaydigan qilib yozilgan (bu **obfuskatsiya** deyiladi): zararli dastur
yaratuvchilari antivirusdan yashirinish uchun, kompaniyalar esa kodini o'g'irlatmaslik uchun shunday qiladi. Tahlilchi
(reverse engineer) bunday dasturni IDA yoki Ghidra bilan ochganda **chigal psevdokod** ko'radi. Uni qo'lda tushunish soatlar,
ba'zan kunlar oladi.

**Biz nima qurdik.** `deobf-agent` — chigal psevdokodni oladigan va:

1. uni **soddalashtiradi** (chalkashliklarni topadi va olib tashlaydi);
2. **toza C kodini** yaratadi;
3. har bir blokni **o'zbek tilida tushuntiradi** — ikki darajada: mutaxassis uchun va "dehqoncha" (kompyuterni bilmaydigan
   odam uchun);
4. natijani **o'zi tekshiradi**: yangi kodni kompilyatsiya qiladi va eski kod bilan minglab tasodifiy kirishda solishtiradi.

**Ikki ishlash usuli.**

| | Offline (bepul) | Claude (pullik) |
|---|---|---|
| Kim soddalashtiradi | oldindan yozilgan qoidalar (Python) | sun'iy intellekt (Claude Sonnet 5.5) |
| Narx | $0 | ≈ $0.03 / funksiya (5 ta funksiyada o'lchangan: $0.024–0.039) |
| Kuchli tomoni | tez, bepul, har doim bir xil natija | mazmunli nom beradi, murakkabroq kodni tushunadi |
| Zaif tomoni | faqat tanish shakllarni biladi | ba'zan xato qiladi — shuning uchun tekshiruv bor |

**Qanday ko'rsatkichlar.** 8 ta test namunasida: 8/8 tasi eski kod bilan bir xil ishlashi tasdiqlandi; kod murakkabligi
58 → 21 ga kamaydi (−64%); qatorlar soni 216 → 95 (−56%). 102 ta avtomatik test o'tadi. 21 ta realistik IDA/Ghidra kirishida
(61 ta funksiya) noto'g'ri natija (mismatch) 0 ta.

**Qanday ishlaydi.** Web sahifa (brauzerda) va buyruq qatori (terminalda) ikkalasi bor. Internetga chiqarish uchun
tayyorlangan: **yopiq demo** (kirish kodi bilan, Claude sizning kalitingiz bilan, to'liq tekshiruv) — lekin Render'da
**hali joylanmagan**, buni faqat siz qila olasiz (12-bo'limga qarang).

**Eng muhim halol gap.** Loyihaning oxirgi bosqichida 5 ta mustaqil "tekshiruvchi" kodni sinab chiqdi va bizning
"tasdiqlandi" degan natijamiz **ba'zi hollarda yolg'on ishonch bergani**ni topdi. Biz buni tuzatdik (9-bo'lim). Bu
hujjatda hech narsa yashirilmagan: nima ishlashi ham, nima ishlamasligi ham yozilgan.

---

## 2. Lug'at: har bir atama nima va nega kerak

Har bir atamada uch narsa: **Nima bu?** → **Nega kerak?** → **Loyihada qayerda?**

### 2.1. Dasturlar va ularni tahlil qilish

| Atama | Nima bu? | Nega kerak / loyihada qayerda |
|---|---|---|
| **Kompilyator** (gcc) | Odam yozgan kodni (C tili) kompyuter tushunadigan 0 va 1 larga aylantiradigan tarjimon. | Biz yangi kodni gcc bilan kompilyatsiya qilib ko'ramiz: kompilyatsiya bo'lmasa — kod xato. `compiler.py`. |
| **Binar fayl** (.exe, .elf) | Kompilyatsiya qilingan, tayyor dastur. Ichida odam o'qiy oladigan kod yo'q, faqat raqamlar. | Test namunalarimiz binar fayllar (`samples/bin/*.elf`). |
| **Dekompilyator** (IDA, Ghidra, angr) | Teskari tarjimon: binardan odam o'qiy oladigan koddan o'xshashini tiklaydi. | Bizning vosita aynan shu dekompilyatorlar chiqargan matnni oladi. |
| **IDA / Hex-Rays** | Pullik, juda mashhur dekompilyator (siz IDA Free ishlatasiz). | Kirish uslublaridan biri. |
| **Ghidra** | AQSh Milliy xavfsizlik agentligi (NSA) ochiq chiqargan bepul dekompilyator. | Kirish uslublaridan biri. |
| **angr** | Python kutubxonasi, binarni tahlil qiladi va dekompilyatsiya qila oladi. | Test namunalarimizni **avtomatik** dekompilyatsiya qilish uchun ishlatdik, chunki IDA ni qo'lda ochish kerak. `scripts/decompile_angr.py`. |
| **Psevdokod** | Dekompilyator chiqargan C ga o'xshash matn. U *deyarli* C, lekin to'liq emas: nomlar (`v1`, `a2`) ma'nosiz, ba'zi turlar (`_DWORD`, `__int64`) oddiy C da yo'q. | Vositaning kirishi. Parser uni tushunadi (`parser.py`), `re_types.h` esa bu turlarni gcc ga tanishtiradi. |
| **Reverse engineering** (teskari muhandislik) | Tayyor dasturdan uning qanday ishlashini tiklash. | Mavzuning o'zi. Masalan, antivirus mutaxassisi zararli dastur nima qilishini shunday aniqlaydi. |

### 2.2. Obfuskatsiya va uning usullari

**Obfuskatsiya** — dastur ishlashi o'zgarmasdan, uni *o'qish* qiyinlashtirilishi. Oshxona misoli: palov baribir palov, lekin
retsept shunday chigal yozilganki, tushunib bo'lmaydi. Biz oltita usulni taniymiz:

| Usul | Nima qiladi? | Misol | Biz nima qilamiz |
|---|---|---|---|
| **MBA** (mixed boolean-arithmetic — aralash mantiqiy-arifmetik ifoda) | Oddiy hisobni uzun, bit amallari aralashgan ifodaga aylantiradi. | `(a ^ b) + 2*(a & b)` aslida oddiygina `a + b` | Ifodani qisqa shaklga almashtiramiz va **minglab tasodifiy sonlarda** bir xil natija berishini tekshiramiz. |
| **Opaque predicate** (soxta shart) | Javobi har doim bir xil bo'ladigan, lekin murakkab ko'rinadigan shart. | `if (x*(x+1) % 2 == 1)` — ketma-ket ikki sonning ko'paytmasi doim juft, demak shart hech qachon rost emas | Shartni `0` yoki `1` ga almashtiramiz va hech qachon bajarilmaydigan kodni olib tashlaymiz. |
| **Control-flow flattening** (boshqaruv oqimini tekislash) | Dasturning tartibli tuzilmasi (`if`, `while`) buziladi: hamma qism bitta katta `while(1){ switch(holat){...} }` ichiga solinadi. | Palov retsepti raqamli kartochkalarga bo'linib, aralashtirib tashlangandek | Holatlar orasidagi o'tishlarni graf sifatida tahlil qilib, `while` va `if` ni qayta tiklaymiz (`unflatten.py`). |
| **Kodlangan satr** | Matn (masalan, parol xabari) kalit bilan "qulflab" saqlanadi va faqat ishlayotganda ochiladi. | baytlar `XOR 0x5C` bilan yashirilgan | Kalitni topib, matnni ochamiz (kalitni kodning o'zidan qidiramiz; topilmasa 255 ta kalitni sinaymiz). |
| **Yashirilgan konstanta** | Son to'g'ridan-to'g'ri yozilmaydi, bir necha sondan hisoblanadi. | `0x7A1C3E55 ^ 0xFB00A390` | Hisobni bajarib, tayyor sonni qo'yamiz. |
| **O'lik kod** | Hisoblanadi, lekin natijaga hech qanday ta'sir qilmaydigan qatorlar. | `junk = x * 7;` — `junk` hech qayerda ishlatilmaydi | Olib tashlaymiz. |

Yettinchi detektor — **mashhur konstantalar** (FNV, CRC-32 kabi). Bu chalkashtirish emas, aksincha **foydali iz**: kodda
`2166136261` sonini ko'rsak, funksiya FNV xesh algoritmiga o'xshashini taxmin qilamiz.

### 2.3. Sun'iy intellekt va API

| Atama | Nima bu? | Nega / qayerda |
|---|---|---|
| **LLM** (Large Language Model) | Katta til modeli: juda ko'p matn va koddan o'rgangan sun'iy intellekt. | Chalkash kodga qarab "bu aslida nima qilyapti" deb tushunadi va nom beradi. |
| **Claude** | Anthropic kompaniyasining LLM'i. Bizda 3 ta model: Haiku (arzon), **Sonnet 5.5 (standart)**, Opus (eng kuchli). | `llm.py` |
| **API** | Dastur boshqa dastur xizmatidan foydalanishi uchun "eshik". Biz Claude'ga **dastur ichidan** so'rov yuboramiz (brauzer chatidan emas). | `llm.py` ichida `anthropic` kutubxonasi orqali. |
| **API kalit** | Parol kabi uzun matn (`sk-ant-...`). Kim so'rov yuborayotganini va **pulni kim to'layotganini** bildiradi. | Kalit sizniki — uni hech kimga bermang, internetdagi serverga yozmang (12–13 bo'lim). |
| **Token** | Modelning matnni o'qish "bo'lagi" (taxminan 3–4 harf). **Narx tokenlar soniga qarab** hisoblanadi: kirish va chiqish alohida. | `PRICES` jadvali va hisobotdagi "narx" ustuni. |
| **Prompt** | Modelga beriladigan ko'rsatma. | `prompts.py`: modelga "sen reverse-engineering yordamchisisan, mana qoidalar..." deb aytiladi. |
| **Structured output** (tuzilgan javob) | Model javobini erkin matn emas, **aniq shakldagi** (maydonlari belgilangan) javob sifatida beradi. | `schema.py`: javob `c_code`, `blocks`, `summary` va h.k. maydonlarda keladi. Erkin matnni dastur o'qiy olmaydi, tuzilgan javobni oladi. |
| **pydantic** | Python kutubxonasi: ma'lumot shaklini tekshiradi. | Model javobi sxemaga mos kelmasa, darrov bilamiz. |
| **Prompt caching** | Bir xil boshlang'ich matnni API serveri eslab qoladi; takroran yuborilganda ~10 baravar arzon. | Tuzatish urinishlarida (bir suhbatning davomida) tejaydi. |
| **Disk kesh** | Bir xil so'rovga javobni diskka yozib qo'yamiz; qayta so'ralsa — bepul. | `.deobf_cache/` |
| **Effort** | Modelning "o'ylash chuqurligi" (past / o'rta / yuqori). Yuqori = sifatliroq, lekin qimmatroq va sekinroq. | `--effort` |
| **Agent** | Natijani **o'zi tekshiradigan** va xato bo'lsa o'z harakatini o'zgartiradigan dastur. Oddiy chatbot javobni bir marta beradi va tamom. | `agent.py` — pastda 6.8. |

### 2.4. Tekshirish

| Atama | Nima bu? | Nega / qayerda |
|---|---|---|
| **Ekvivalent kod** | Har qanday kirishga **bir xil natija** beradigan kod (garchi yozilishi boshqacha bo'lsa ham). | Soddalashtirilgan kod asl bilan ekvivalent bo'lishi shart. |
| **Differensial test** | Ikki funksiyani **bir xil tasodifiy kirishlar** bilan minglab marta chaqirib, natijalarni solishtirish. | Eng asosiy tekshiruv. `harness.py`. Farq chiqsa — kod noto'g'ri. |
| **Isbot emas, dalil** | Tasodifiy test "hamma kirishlarda to'g'ri" deb *isbotlay olmaydi*; faqat "2000 tasida to'g'ri" deydi. Isbot uchun SMT-yechuvchi (Z3) kabi matematik vosita kerak. | Shuning uchun hisobotda "**Tasdiqlandi**" deymiz-u, "isbotlandi" demaymiz. |
| **Segfault / SIGSEGV** | Dastur ruxsat etilmagan xotiraga tegib qulashi. | Test dasturida qulashni "ushlab" olamiz va keyingi testga o'tamiz. |

### 2.5. Veb va xavfsizlik

| Atama | Nima bu? | Nega / qayerda |
|---|---|---|
| **Flask** | Python'da veb-sayt yasash kutubxonasi. | `web/app.py` |
| **Jinja (shablon)** | HTML ichiga ma'lumot qo'yadigan shablon tizimi. | `web/templates/*.html`. U matnni avtomatik **ekranlaydi**. |
| **XSS** | Hujumchi sahifaga zararli skript kiritishi. | Model va foydalanuvchi matni **doim ekranlanadi** (`|safe` hech qayerda yo'q). |
| **CSRF** | Boshqa sayt sizning nomingizdan so'rov yuborishi. | `Origin`/`Host`/`Sec-Fetch-Site` tekshiruvi (11-bo'lim). |
| **DNS rebinding** | Boshqa sayt brauzeringiz orqali `localhost` dagi serverga murojaat qilishi. | `Host` sarlavhasi tekshiriladi. |
| **CSP** (Content-Security-Policy) | Brauzerga "faqat shu manbalardan skript yukla" degan qoida. | `script-src 'self'`: faqat o'zimizning skriptlar. |
| **BYOK** (bring your own key) | "Kalitingizni o'zingiz olib keling". Server kalit saqlamaydi, foydalanuvchi o'z kalitini kiritadi. | Public rejim. Aks holda har bir begona sizning pulingizdan foydalanadi. |
| **Rate limit** | Bir odam qisqa vaqtda ko'p so'rov yubora olmasligi. | Public demoda 10 daqiqada 15 tahlil. |
| **Sandbox** | Dasturni "qum qutisida" — cheklangan muhitda ishga tushirish. | `sandbox.py`. Pastda: nega yetarli emas (11-bo'lim). |
| **Nonce** | Faqat bir marta ishlatiladigan tasodifiy so'z. | Test dasturi natija satrlariga qo'shadi: tekshirilayotgan kod soxta natija yoza olmasligi uchun. |
| **Sessiya va cookie** | Saytga kirganingizni brauzer "eslab qolishi": kirgandan keyin server sizga imzolangan kichik belgi (cookie) beradi. | Kirish kodini har bosishda so'ramaslik uchun. `HttpOnly` — skript uni o'qiy olmaydi; `Secure` — faqat HTTPS orqali yuboriladi. |
| **Brute force** (qo'pol kuch) | Parolni hamma variantni birma-bir sinab topish. 4 xonali kodda 10 000 variant bor. | Urinishlar cheklangan (bitta IP'dan 15 daqiqada 5 ta; jami soatiga 40 ta). |
| **Foydalanuvchi ajratish (uid)** | Operatsion tizimda har bir dastur ma'lum foydalanuvchi huquqi bilan ishlaydi. Huquqsiz foydalanuvchi boshqa foydalanuvchining jarayoni va maxfiy qiymatlarini o'qiy olmaydi. | Tekshirilayotgan kod serverning API kalitini o'qiy olmasligi uchun (`DEOBF_SANDBOX_UID`). |
| **`sync: false`** (render.yaml) | "Bu qiymatni faylda saqlama, Render'da men kiritaman." | Parol va kalit GitHub'ga tushmasligi uchun. |
| **Kunlik byudjet** | Bir kunda Claude uchun sarflanadigan eng ko'p pul. | Kod qo'lga tushsa ham pul cheksiz ketmasligi uchun. |

### 2.6. Joylash (deploy)

| Atama | Nima bu? | Nega kerak |
|---|---|---|
| **Deploy** | Dasturni internetdagi serverga qo'yib, hamma ochishi mumkin qilish. | Ustoz va boshqalar havola orqali ko'ra olishi uchun. |
| **Docker / konteyner** | Dastur va uning hamma kerakli narsalarini bitta "quti"ga solish: qayerda ochilsa ham bir xil ishlaydi. | `Dockerfile` — qutini qanday yig'ishni tasvirlaydi. |
| **gunicorn** | Internet uchun mo'ljallangan Python veb-serveri. Flask'ning o'z serveri faqat sinash uchun. | `Dockerfile` oxirida. |
| **WSGI** (`wsgi.py`) | Veb-ilovani gunicorn'ga ulaydigan standart "rozetka". | `wsgi.py` |
| **Render** | Bepul reja bor bulutli xosting. GitHub'dagi kodni olib, Docker'dan ishga tushiradi. | `render.yaml` |
| **Muhit o'zgaruvchisi** | Dastur tashqaridan oladigan sozlama (`DEOBF_PUBLIC=1`). Parol va rejimlar kodga yozilmaydi. | public rejim shu bilan yoqiladi. |
| **Proksi / X-Forwarded-For** | Render so'rovni o'z serveri orqali o'tkazadi; haqiqiy mijoz IP'si shu sarlavhada keladi. | Rate limit haqiqiy IP bo'yicha ishlashi uchun (`DEOBF_TRUSTED_PROXIES`). |

---

## 3. Topshiriq nima edi va biz uni qanday hal qildik

Mavzu matnida uchta talab bor. Har biriga javob:

| # | Talab | Qaysi modul hal qiladi | Qanday |
|---|---|---|---|
| 1 | **Obfuskatsiyalangan kodni LLM yordamida soddalashtirish** | `prompts.py`, `llm.py`, `schema.py` (Claude); `detectors.py`, `offline.py`, `unflatten.py` (LLM'siz) | Statik tahlil chalkashlikni topadi, so'ng Claude yoki qoidalar soddalashtiradi. |
| 2 | **C tilidagi ekvivalentini yaratish** | `verifier.py`, `harness.py`, `compiler.py`, `agent.py` | Yaratilgan C kod gcc bilan kompilyatsiya qilinadi va asl kod bilan **minglab tasodifiy kirishda** solishtiriladi. "Ekvivalent" so'zi shu tekshiruv bilan asoslanadi. |
| 3 | **Har bir blokni inson tushunadigan tilda tushuntirish** | `narrate.py`, `blocks.py`, `explain.py`, `report.py`, `web/` | Har bir blok uchun: sarlavha, mutaxassis izohi, "dehqoncha" izohi, oldin/keyin kodi. |

Qo'shimcha (siz so'ragan): **arzon** bo'lishi (Haiku/Sonnet tanlash, kesh, bepul offline), **IDA va Ghidra** bilan ishlashi
(eksport skriptlari), **CLI + Web UI**, **internetga chiqarish**, **murakkabroq kod** (bufer, bir nechta funksiya),
**"dehqoncha"** tushuntirish.

---

## 4. Umumiy sxema: ma'lumot qanday oqadi

```
 IDA / Ghidra / angr psevdokodi (matn)
              │
              ▼
 ┌─────────────────────────┐
 │ parser.py               │  Matnni funksiyalarga ajratadi, uslubni (IDA/Ghidra/angr/C) aniqlaydi
 └────────────┬────────────┘
              ▼
 ┌─────────────────────────┐
 │ detectors.py + expr.py  │  STATIK TAHLIL (Claude'siz, bepul): MBA, soxta shart, tekislash,
 │                         │  kodlangan satr, o'lik kod... topadi va tasodifiy test bilan tasdiqlaydi
 └────────────┬────────────┘
              ▼
      ┌───────┴────────┐
      ▼                ▼
 OFFLINE rejim      CLAUDE rejimi
 offline.py         prompts.py ─► llm.py ─► Claude API
 unflatten.py       (xabar tuzadi)   (javob: C kod + bloklar)
      └───────┬────────┘
              ▼
 ┌─────────────────────────────────────┐
 │ verifier.py + harness.py + compiler │  1) gcc kompilyatsiya qiladimi?
 │                                     │  2) asl kod bilan 2000 tasodifiy kirishda bir xilmi?
 └────────────┬────────────────────────┘
              │ xato bo'lsa: xatoni Claude'ga qaytaradi (ko'pi bilan 3 marta)
              ▼
 ┌─────────────────────────┐
 │ agent.py                │  Eng yaxshi natijani tanlaydi (Claude yoki offline)
 └────────────┬────────────┘
              ▼
 ┌─────────────────────────────────────┐
 │ narrate.py + blocks.py + explain.py │  Har bir blok uchun tushuntirish (mutaxassis + dehqoncha)
 └────────────┬────────────────────────┘
              ▼
 report.py ──► Markdown / JSON / HTML        cli.py (terminal)        web/app.py (brauzer)
```

**Nega aynan shunday tartib?** Eng arzon va ishonchli qadamlar (parser, statik tahlil) **avval** bajariladi; qimmat qadam
(Claude) **keyin**; eng muhim qadam (tekshiruv) **oxirida** — chunki Claude xato qilishi mumkin, uning javobiga ko'r-ko'rona
ishonib bo'lmaydi.

---

## 5. Fayllar va ularning vazifalari

Loyiha papkasi: `deobf_agent/` (asosiy dastur, 23 ta Python fayli, ~6000 qator), `tests/` (testlar), `samples/` (test
namunalari), `docs/` (hujjatlar), `scripts/` (yordamchi skriptlar).

### 5.1. Asosiy modullar (`deobf_agent/`)

| Fayl | Qator | Vazifasi (bir jumlada) | Nega alohida fayl? |
|---|---|---|---|
| `models.py` | 62 | Hamma modul ishlatadigan ma'lumot "qutilari": funksiya, parametr, topilma. | Modullar bir-biriga bog'lanib qolmasligi uchun umumiy til. |
| `parser.py` | 256 | Psevdokod matnini funksiyalarga ajratadi; qaysi dekompilyatordan ekanini aniqlaydi. | Kirish har xil ko'rinishda (IDA, Ghidra...) — bir joyda hal qilinadi. |
| `expr.py` | 578 | C ifodalarini Python ichida hisoblaydigan "kalkulyator" (razryad va ishorani hisobga oladi). | MBA ifoda ekvivalentligini **tasodifiy sonlar bilan sinash** uchun. |
| `detectors.py` | 687 | 7 ta detektor: chalkashlikni topadi. | Claude'siz, bepul ishlaydigan "ko'z". |
| `unflatten.py` | 285 | Tekislangan kodni (`while(1){switch}`) tartibli `while/if` ga qaytaradi. | Eng qiyin chalkashtirish; alohida algoritm. |
| `offline.py` | 329 | Claude'siz soddalashtirish: ifodalarni almashtiradi, o'lik kodni olib tashlaydi. | Bepul rejim va Claude xato qilgandagi zaxira. |
| `schema.py` | 47 | Claude javobining shakli (`c_code`, `blocks`, `summary`, `simple_summary`...). | Javob dastur o'qiydigan aniq shaklda kelishi uchun. |
| `prompts.py` | 179 | Claude'ga ko'rsatma (qoidalar) va xabar tuzish. | Natija sifati shu matnga bog'liq — alohida ushlash oson. |
| `llm.py` | 369 | Claude API bilan ishlash: so'rov, narx, kesh, xatolarni tushunarli qilish, kalit xavfsizligi. | API'ga oid hamma narsa bir joyda. |
| `compiler.py` | 135 | gcc bilan ishlash; IDA/Ghidra'ga xos yozuvlarni (`i64`, `@<eax>`) gcc tushunadigan qiladi. | Kompilyatsiya tafsilotlari boshqa modullarni ifloslantirmasligi uchun. |
| `harness.py` | 732 | **Differensial test**: ikki funksiyani solishtiradigan C test dasturini yasaydi va ishga tushiradi. | Loyihaning "ishonch" yuragi. |
| `verifier.py` | 155 | Tekshiruv bosqichlari: kompilyatsiya → imzo → differensial test; natijani 5 holatdan biriga keltiradi. | Tekshiruv mantig'i (nima "yaxshi" hisoblanadi) alohida. |
| `agent.py` | 209 | Hammasini birlashtiradi: Claude → tekshiruv → xato bo'lsa qayta urinish → zaxira. | "Agent" xatti-harakati shu yerda. |
| `explain.py` | 99 | Tushuntirish matnlari: usullarning nomlari va "dehqoncha" o'xshatishlar. | Matnlar kodga aralashib ketmasin. |
| `narrate.py` | 785 | Tozalangan koddan **aniq o'zbekcha jumlalar** yasaydi va funksiya nima hisoblashini aniqlaydi (EKUB, FNV, saralash...). | Offline rejimda ham har bir blok tushunarli bo'lishi uchun. |
| `blocks.py` | 191 | Offline rejim uchun bloklarni yig'adi: kod qadamlari + olib tashlangan narsalar. | `narrate.py` jumlalarini bloklarga bog'laydi. |
| `metrics.py` | 31 | Kod murakkabligini o'lchaydi (qatorlar, tsiklomatik murakkablik). | "Soddalashtirish qancha foyda berdi?" degan savolga raqam bilan javob. |
| `report.py` | 164 | Natijani Markdown / JSON / HTML hisobotga aylantiradi. | Natijani saqlash va ko'rsatish. |
| `evaluate.py` | 115 | Namunalar bo'yicha avtomatik baholash (`deobf eval`). | Natijani raqamlarda ko'rsatish. |
| `sandbox.py` | 105 | Tashqi dasturlarni (gcc, test) cheklangan muhitda ishga tushiradi; public rejimda ishga tushirishni o'chiradi. | Xavfsizlik. |
| `cli.py` | 241 | Buyruq qatori: `deobf analyze`, `web`, `check`, `eval`, `functions`. | Terminaldan foydalanish. |
| `web/app.py` | 236 | Web UI serveri (Flask) va public rejim himoyalari. | Brauzerdan foydalanish. |
| `web/templates/`, `web/static/` | — | Sahifa shablonlari, uslub (CSS), brauzer skriptlari, `highlight.js` (kod ranglash). | Interfeys. |
| `data/re_types.h` | — | C sarlavha fayli: `_DWORD`, `__int64`, `undefined4` kabi IDA/Ghidra turlarini gcc'ga tanishtiradi. | Psevdokod gcc'da kompilyatsiya bo'lishi uchun. |

### 5.2. Boshqa papkalar

| Joy | Nima | Vazifasi |
|---|---|---|
| `samples/src/clean/` | 8 ta **toza** C funksiya | "To'g'ri javob" — vosita natijasini shu bilan solishtiramiz. |
| `samples/src/obf/` | Xuddi shu funksiyalarning **obfuskatsiyalangan** varianti | Vositaning kirishi uchun chalkash kod. |
| `samples/bin/` | Kompilyatsiya qilingan binarlar (.elf) | Dekompilyator uchun xom material. |
| `samples/decompiled/` | angr dekompilyatsiya qilgan psevdokod | Vositaning real kirishi. |
| `scripts/` | `build_samples.py`, `decompile_angr.py`, `ida_export.py`, `ghidra_export.java` | Namunalarni yig'ish; IDA va Ghidra'dan psevdokodni eksport qilish. |
| `tests/` | 102 ta avtomatik test (10 fayl) | Kod buzilmaganini har safar tekshiradi. |
| `docs/` | Hujjatlar (00–06) | Tushuntirishlar, jurnal, yo'riqnoma, hisobot. |
| `Dockerfile`, `render.yaml`, `wsgi.py`, `.dockerignore` | Joylash fayllari | Internetga chiqarish. |
| `*.bat` | Windows uchun ikki marta bosiladigan fayllar | O'rnatish, kalit kiritish, ishga tushirish, tekshirish. |

### 5.3. 8 ta test namunasi

| Namuna | Funksiya | Qanday chalkashtirish | Nima uchun |
|---|---|---|---|
| s1_mba | `mix` | MBA ifodalar | Eng sodda: ifoda soddalashtirish. |
| s2_opaque | `clamp` | soxta shartlar | Hech qachon bajarilmaydigan tarmoq. |
| s3_flatten | `gcd` (EKUB) | tekislash | Boshqaruv oqimini tiklash. |
| s4_strings | `greet_char` | kodlangan matn | Yashirin matnni ochish. |
| s5_combined | `checksum` (FNV-1a) | hammasi birga | Real hayotga yaqin. |
| s6_buffer | `xor_stream` | bufer + tekislash | Ko'rsatkich (bufer) parametri. |
| s7_calls | `rotl32`, `rot_hash` | ikki funksiya | Funksiya boshqa funksiyani chaqirishi. |
| s8_sort | `bubble_sort` | ichma-ich tsikllar + tekislash | Massivni joyida o'zgartirish. |

---

## 6. Har bir qism qanday ishlaydi (chuqur)

### 6.1. Parser (`parser.py`)

**Vazifasi:** kirish matnidan funksiyalarni ajratib olish.

**Qanday:** matndagi `{` va `}` qavslar juftini sanab funksiya tanasini topadi. Izoh va qator ichidagi matnni vaqtincha
"niqoblaydi" (bo'sh joyga almashtiradi), shunda matn ichidagi qavs adashtirmaydi. Keyin imzo (`int f(int a)`) dan nom, qaytish
turi va parametrlarni oladi. Uslubni ball tizimi bilan aniqlaydi: `sub_401136` va `_DWORD` — IDA; `FUN_` va `undefined4` — Ghidra.

**Nega kerak:** hamma keyingi qadamlar funksiya *chegarasini* bilishi shart. Bitta faylda ko'p funksiya bo'lsa, ularni
alohida tahlil qilamiz (chaqirilganlarini avval).

**Audit topgan va tuzatilgan xato:** `__attribute__((noinline))`, `__declspec(dllexport)` va IDA'ning `name@<rax>` yozuvi
bilan boshlangan funksiyalar **indamay tashlab yuborilar edi**.

### 6.2. Ifoda kalkulyatori (`expr.py`)

**Vazifasi:** `(a ^ b) + 2*(a & b)` kabi ifodani Python'da **C qoidalari bo'yicha** hisoblash.

**Nega oddiy Python yetmaydi:** C da sonning **razryadi** (32 yoki 64 bit) va **ishorasi** (manfiy bo'la oladimi) natijani
o'zgartiradi. Masalan, `unsigned` 32-bitli `0 - 1` = 4294967295, Python'da esa `-1`. Shuning uchun kalkulyator har bir
o'zgaruvchining turini kuzatadi.

**Tasodifiy sinov:** ifodani 2000–3000 ta tasodifiy qiymat bilan hisoblaymiz. Qiymatlarning bir qismi **koddagi sonlardan**
olinadi (chunki `x == 0x1337BEEF` kabi shart tasodifiy sonda deyarli hech qachon rost bo'lmaydi).

**Muhim ehtiyot (audit ortidan):** shart "doim yolg'on" deb faqat *taqqoslanayotgan qiymat kam turli qiymat olsa*
hisoblanadi. Aks holda `a1 == 1337 && a2 == 31337` kabi **haqiqiy mantiq** soxta shart sifatida o'chib ketardi.

### 6.3. Statik tahlil (`detectors.py`)

**Vazifasi:** Claude'siz chalkashlikni topish. Har bir detektor `Finding` ("topilma") qaytaradi: qaysi usul, qaysi qatorda,
xabar, soddalashtirilgan variant, tasodifiy test bilan tasdiqlanganmi.

**Nega Claude'siz?** (1) bepul; (2) har doim bir xil natija; (3) topilmalar Claude'ga **dalil** sifatida beriladi
("bu ifoda MBA, TASDIQLANGAN") — u ko'proq ishonadi va xato qilishi kamayadi.

### 6.4. Offline soddalashtirish (`offline.py`)

**Vazifasi:** qoidalar bilan kodni o'zgartirish. **To'rt daraja** (xavfsizlikdan kuchligacha):

| Daraja | Nima qiladi |
|---|---|
| 2 | tekislashni yechadi + soxta tarmoqlarni kesadi + o'lik kodni olib tashlaydi (eng kuchli) |
| 1 | tekislashsiz, lekin tarmoq va o'lik kod bilan |
| 0 | faqat ifodalarni soddalashtiradi |
| −1 | **hech narsa o'zgartirmaydi** (kod aslidek, tushuntirish bor) |

**Nega daraja?** Agent eng kuchlisidan boshlaydi; natija tekshiruvdan o'tmasa, ehtiyotkorroq darajaga tushadi. −1 daraja
**oxirgi himoya**: noto'g'ri kod chiqarishdan ko'ra, kodni o'zgartirmaslik yaxshi.

**Soddalashtirish qoidalari (audit ortidan):** natija **turi** saqlanadi (cast qo'shiladi); `i++` kabi yon ta'sirli ifodalar va
funksiya chaqiruvlari **tegilmaydi**; `else` qoldiqlari tozalanadi; keyingi o'qishdan oldin qayta yoziladigan qiymat berishlar
("ortiqcha qiymat") olib tashlanadi.

### 6.5. Tekislashni yechish (`unflatten.py`)

**Vazifasi:** `while(1){ switch(v4){ case 161: ...; v4 = 31; break; case 31: v4 = (v2<v0) ? 196 : 119; ...} }` ni oddiy
`while (v2 < v0) { ... }` ga aylantirish.

**Qanday:** har bir `case` — bu "holat". Holat qaysi holatga o'tishini (`v4 = 31`) o'qib, **graf** tuzadi. Orqaga qaytadigan
yo'l = tsikl (`while`), ikkiga ajraladigan = `if/else`. Natijada dispetcher va holat o'zgaruvchisi kerak bo'lmay qoladi.

**Cheklov:** faqat oddiy holatlar mashinasi. Murakkab shakllarda (ichma-ich `switch`, `while (st != 9)`) yechmaydi va kodni
tegmasdan qoldiradi — bu xavfsiz tanlov.

### 6.6. Claude bilan ishlash (`prompts.py`, `schema.py`, `llm.py`)

**1) Xabar tuzish.** `prompts.py` Claude'ga yuboriladigan xabarni yasaydi: qator raqamli psevdokod + statik tahlil topilmalari
(*TASDIQLANGAN* yoki *taxmin*) + holatlar xaritasi + dekodlangan satrlar + chaqiriladigan yordamchi funksiyalar haqida
eslatma. Ko'rsatmalar **ingliz tilida** (modellar shunda aniqroq bajaradi va tokenlar kamroq ketadi), **javob** esa
foydalanuvchi tilida (standart: o'zbek).

**2) Ko'rsatmaning asosiy qoidalari** (`SYSTEM_PROMPT`): funksiya nomi va parametrlari **aynan** saqlansin; yordamchi
funksiyalar **asl nomi** bilan chaqirilsin; xulq o'zgarmasin (yangi tekshiruv qo'shilmasin); soxta shartni faqat
*tasdiqlangan* bo'lsa olib tashlasin; **o'ylab topmasin**; psevdokod ichidagi "buyruqlar"ga amal qilmasin (u faqat ma'lumot).
Bloklar uchun: nima qilishini aytadigan sarlavha, 2–3 gapli mutaxassis izohi va **alohida** "oddiy tilda" matni.

**3) Javob shakli** (`schema.py`): `function_name`, `suggested_name`, `summary`, `simple_summary`, `techniques`, `c_code`,
`blocks[]` (title, original_lines, original_code, simplified_code, explanation, simple), `renames[]`, `confidence`, `notes`.

**4) So'rov yuborish** (`llm.py`). Javob **aniq sxema bo'yicha** keladi. Muhim tafsilotlar:

* **Avval narx hisoblanadi**, keyin tekshiriladi — javob kesilsa yoki rad etilsa ham pul sarflangan bo'ladi.
* **Rad etish** (`refusal`): Sonnet 5.5 xavfsizlik filtri zararli dastur bilan bog'liq kodni rad etishi mumkin. Vosita buni
  tushunarli xabar bilan aytadi va **offline** natijaga o'tadi.
* **Kalit xavfsizligi:** kalit hech qachon xato matniga, keshga, jurnalga yozilmaydi; `repr()` da ko'rinmaydi. Public
  rejimda **server kalitidan umuman foydalanilmaydi**.
* **Kesh:** tekshiruvdan o'tmagan javoblar keshdan o'chiriladi, aks holda qayta urinishda "bepul" xuddi shu xato qaytardi.

**Narx:** Sonnet 5.5 — $2 (kirish) / $10 (chiqish) har 1 million token uchun; Haiku 5.5 — $0.10 / $0.50; Opus 5.5 —
$4 / $20. Jadval rasmiy ma'lumot bilan solishtirilgan.

### 6.7. Tekshiruv (`verifier.py`, `harness.py`, `compiler.py`)

**Uch bosqich:**

1. **Sintaksis:** yangi kod gcc'da kompilyatsiya bo'ladimi?
2. **Imzo:** funksiya nomi, parametrlar soni **va turlarining kengligi** (`int` o'rniga `short` emas) asldagidek ekanmi?
3. **Xatti-harakat (differensial test):** asl va yangi funksiya bir xil kirishlarda bir xil natija beradimi?

**Differensial test qanday ishlaydi (`harness.py`).** Vosita **C tilida kichik test dasturi** yozadi, u:

* ikkala funksiyani bitta dasturga birlashtiradi (nomlar to'qnashmasligi uchun qayta nomlanadi);
* 2000 marta tasodifiy kirish yasaydi va **ikkalasini bir xil kirish bilan** chaqiradi;
* qaytish qiymatini, **bufer mazmunini**, **global o'zgaruvchilarni** va **tashqi funksiyalar chaqiruvlari ketma-ketligini**
  solishtiradi;
* birorta farq topilsa — `mismatch`.

**Kirishlar qanday tanlanadi** (bu juda muhim, chunki test sifati shunga bog'liq):

* chegaraviy qiymatlar (0, 1, 255, 2³¹−1, −1...) va tasodifiy sonlar aralashmasi;
* koddagi **literallar** (`0x1337BEEF`, `'q'`) va ularning qo'shnilari (c, c±1, −c);
* har sakkizinchi testda parametrlarga koddagi literallar **ketma-ket** beriladi (`a == K1 && b == K2` kabi shartlar uchun);
* bufer parametri bo'lsa: har bir bufer **4096 bayt**, tasodifiy / matn / nolli to'ldirilgan, chetlari **qo'riqchi sahifa**
  bilan o'ralgan (chegaradan chiqish darhol ushlanadi).

**Himoyalar:**

* **Qulash/osilish ushlanadi** (`sigsetjmp`, har chaqiruvga 0.2 s; stek to'lsa ham `sigaltstack` bilan). Asl funksiya
  qulasa — o'sha kirish o'tkaziladi; faqat *yangi* funksiya qulasa — bu **farq**.
* **Soxta natijadan himoya:** test dasturi natija satrlariga tasodifiy so'z (nonce) qo'shadi; tekshirilayotgan kod `RESULT
  tests=2000 mismatches=0` deb o'zi yozib aldab o'ta olmaydi.
* **Erta to'xtash:** 5 ta farq topilsa, davom etishning keragi yo'q.
* **Kam test bo'lsa — ishonmaymiz:** asl funksiya ko'p kirishda qulasa va juda kam test o'tsa, "tasdiqlandi" demaymiz.

**Tashqi funksiyalar va globallar.** Kodda noma'lum funksiya chaqirilsa (masalan, `printf`), uning o'rniga **stub** (soxta
funksiya) qo'yiladi: u argumentlar asosida aniq qiymat qaytaradi va chaqiruvlar tarixini xeshlaydi. Shunda ikkala funksiya
tashqi dunyo bilan **bir xil "muloqot" qilganini** tekshiramiz. IDA/Ghidra'ning global nomlari (`dword_404010`) alohida
modulda bitta nusxada yaratiladi va har chaqiruvdan oldin boshlang'ich holatga qaytariladi.

**5 ta natija holati:**

| Holat | Ma'nosi |
|---|---|
| `verified` — **Tasdiqlandi** | kompilyatsiya bo'ldi va barcha testlar mos keldi (eng yaxshi) |
| `compiled` — Kompilyatsiya bo'ldi | kod to'g'ri, lekin avtomatik solishtirib bo'lmadi (masalan, funksiya ko'rsatkichi parametri) |
| `mismatch` — **Farq bor** | testda farq topildi: natijaga **ishonmang** |
| `compile_error` | kod kompilyatsiya bo'lmadi |
| `no_compiler` — Tekshirilmadi | gcc yo'q yoki public demo (kod ishga tushirilmaydi) |

### 6.8. Agent sikli (`agent.py`) — nega bu "agent"

```
Claude'dan so'raydi → tekshiradi ─┬─ yaxshi ──────────────► tamom
                                  └─ xato ─► xatoni Claude'ga qaytaradi ("mana bu joyda farq bor, tuzat")
                                              (ko'pi bilan 3 urinish)
Agar Claude natijasi "tasdiqlandi" emas bo'lsa → offline natija bilan ham solishtiradi va yaxshisini oladi.
```

**Agent** — chunki u o'z natijasini **tekshiradi** va tekshiruv natijasiga qarab **harakatini o'zgartiradi**. Oddiy
chatbot javobni bir marta berib qo'yadi.

**Muhim qaror:** Claude 3 marta xato qilsa, jim turib noto'g'ri natijani ko'rsatmaymiz. Offline natija **tasdiqlangan**
bo'lsa — o'shani tanlaymiz va sababini hisobotga yozamiz. Ko'p funksiyali kirishda **avval chaqiriladigan** (yordamchi)
funksiyalar tahlil qilinadi va ularning qisqa tavsifi chaqiruvchi funksiya uchun Claude'ga beriladi — odam ham kodni shunday o'qiydi.

### 6.9. Tushuntirish: `narrate.py`, `blocks.py`, `explain.py`

**Muammo (bosqich boshida):** offline rejimda blok sarlavhasi "MBA ifoda" kabi **usul nomi** edi, "oddiy tilda" matni esa har
safar bir xil tayyor paragraf. Bu "har bir blok tushunarli bo'lsin" talabini bajarmasdi.

**Yechim:**

1. `narrate.py` tozalangan funksiyani **daraxtga** ajratadi (shart, tsikl, oddiy gap) va har bir qadam uchun **aniq jumla**
   yasaydi. Ikki xil: mutaxassis (`` `v2` ga `v1` ni `v0` ga bo'lgandagi qoldiqni yozadi``) va oddiy (`«v1» ni «v0» ga
   bo'lganda qoladigan qoldiqni hisoblab, «v2» qutisiga soladi`).
2. U **idiomalarni** taniydi: o'rin almashtirish (`t=a; a=b; b=t`), tsikl hisoblagichi, EKUB, FNV xesh, XOR shifrlash,
   pufakchali saralash, bit aylantirish, oddiy formula. Shunda funksiya xulosasida **nima hisoblashi** aytiladi.
3. `blocks.py` bularni bloklarga yig'adi va **olib tashlangan narsalarni** (keraksiz qatorlar, soxta tarmoqlar, tekislash,
   yashirin matn) alohida bloklar qiladi. Har bir blok asl koddagi qatorlarga bog'lanadi.
4. `explain.py` chalkashtirish usullari uchun **qisqa o'xshatishlar** saqlaydi (bozor, oshxona, xat/qulf).

**"Dehqoncha" qoidalari:** kod belgisi yo'q (backtick, `0x...` yo'q); qisqa gaplar; bitta blokda bitta o'xshatish; hayotiy
obrazlar bir oiladan (bozor / retsept / dala / xat). **Test** (`tests/test_narrate.py`) shuni kafolatlaydi — va u testning
o'zi dastlab xom kod (`*((char*)&v3+...)`) oddiy tilga sizib chiqayotganini topdi.

**Cheklov (halol):** offline rejim faqat **tanish shakllarni** nomlaydi; boshqasini umumiy gap bilan tushuntiradi. Claude rejimi
moslashuvchan. Sifati haqiqiy API bilan 5 funksiyada ko'rildi: hammasi 1-urinishda tasdiqlandi (kichik tanlama, 10.5-bo'lim).

### 6.10. Hisobot (`report.py`)

Bitta natijadan uch format: **Markdown** (GitHub/muharrirda o'qish), **JSON** (boshqa dasturlar uchun), **HTML** (brauzerda;
bitta fayl, internetsiz ochiladi). Matn xavfsiz ko'rsatiladi: avval hammasi ekranlanadi, keyin faqat `` `kod` `` bo'laklari kod
shriftiga o'raladi.

### 6.11. CLI va Web UI (`cli.py`, `web/`)

* **CLI:** `deobf analyze fayl.c` (tahlil), `deobf functions fayl.c` (funksiyalar ro'yxati), `deobf web` (brauzer
  interfeysi), `deobf check` (diagnostika), `deobf eval` (baholash).
* **Web UI:** matn maydoniga psevdokod joylaysiz (yoki fayl/namuna tanlaysiz), model va tilni tanlaysiz, "Tahlil qilish" —
  natija sahifada. **"Mutaxassis uchun / Oddiy tilda"** tugmasi sahifani qayta yuklamasdan almashtiradi.

---

## 7. Bosqichma-bosqich: nima qildik va nega

Har bir bosqich alohida **commit** (saqlash nuqtasi) sifatida GitHub'da. Batafsil kundalik: `docs/01_jurnal.md`.

| Bosqich | Nima qildik | Nega aynan shunday | Vosita |
|---|---|---|---|
| **0. Rejalashtirish** | Mavzuni tushuntirdik, savollar berdik (Claude API, IDA Free, CLI+Web), reja tuzdik. | Avval nima qurayotganimizni va nimaga erishishimizni bilish kerak. | `docs/00` |
| **1. Asos va namunalar** | 5 ta toza funksiya yozdik, har biriga chalkash variant, ikkalasini kompilyatsiya qilib binar oldik, angr bilan dekompilyatsiya qildik. | Test uchun **to'g'ri javob** (toza kod) va **real kirish** (dekompilyator chiqishi) kerak. | gcc, angr, Python |
| **2. Parser** | Psevdokodni funksiyalarga ajratadigan modul. | Hamma narsa funksiya chegarasiga bog'liq. | Python, pytest |
| **3. Statik tahlil** | Ifoda kalkulyatori, 7 detektor, metrikalar. | Claude'siz, bepul "ko'z" + Claude'ga dalil. | Python |
| **4. Claude moduli** | Javob sxemasi, prompt, narx hisoblash, kesh, offline rejim. | LLM'ni boshqariladigan va **arzon** qilish. | `anthropic`, pydantic |
| **5. Tekshiruv va agent** | Kompilyatsiya + differensial test, xato bo'lsa qayta urinish. | LLM xato qiladi — **ishonib bo'lmaydi, tekshirish kerak**. | gcc |
| **6. CLI va Web UI** | Buyruq qatori, hisobot formatlari, Flask sayt. | Foydalanuvchi qulay ishlata olishi uchun. | Flask |
| **7. Baholash va unflatten** | `deobf eval`, tekislashni avtomatik yechish. | Natijani **raqamlarda** ko'rsatish; eng qiyin chalkashtirishni hal qilish. | Python |
| **8. Windows tuzatishlari** | `.env` har qanday kodlashda o'qiladi; `deobf check`; `.bat` fayllar; kalitni tekshirish tugmasi. | Siz ishlatganda dastur ishga tushmadi: PowerShell `.env` ni UTF-16 da yozgan edi. **Haqiqiy foydalanuvchi muhitida sinash zarurligi** saboq bo'ldi. | Python |
| **9. Mukammallashtirish** | Bufer/ko'p funksiya/tashqi chaqiruv bilan ishlash; 3 yangi namuna; UI qayta dizayn; "dehqoncha"; public rejim; Dockerfile. | Siz so'ragan: murakkabroq kod, sodda UI, hamma tushunsin, internetga chiqarish. | Chromium, Docker |
| **10. Mustaqil audit va tuzatishlar** | 5 mustaqil agent kodni sindi; topilgan xatolar tuzatildi; Sonnet 5.5; aniq jumlali bloklar; brauzer sinovi; hujjatlar. | "Xato ketgan joying bormi?" degan savolingiz. Natija — 9-bo'lim. | agentlar, Playwright |
| **11. Joylashga tayyorlik** | Joylash qadamlari qayta ishlab tekshirildi, to'liq tushuntirish (shu hujjat) yozildi. | Ustozga ko'rsatish. | — |
| **12. Yopiq demo** | Siz so'radingiz: "loyiha ishlashi kerak, saytga parol bilan kiradigan qil, API'imni serverga qo'y". Kirish kodi, server kaliti (kunlik byudjet bilan), to'liq tekshiruv alohida huquqsiz foydalanuvchi nomidan, urinishlar cheklovi, 10 ta yangi test. | Ochiq demo "Tekshirilmadi" bo'lib, demo uchun yaroqsiz edi; kirish kodi xavf modelini o'zgartiradi, shuning uchun to'liq ishlashni xavfsiz yoqish mumkin. | Flask sessiya, Docker, Playwright |

---

## 8. Ishlatilgan vositalar

| Vosita | Nima uchun ishlatdik |
|---|---|
| **Python 3** | Loyihaning asosiy tili: o'qish oson, kutubxonalari ko'p. |
| **gcc** | Kodni kompilyatsiya qilish va differensial test dasturini yig'ish. |
| **angr** | Test binarlarini avtomatik dekompilyatsiya qilish. |
| **anthropic (kutubxona)** | Claude API bilan Python'dan ishlash. |
| **pydantic** | Claude javobi shaklini tekshirish. |
| **Flask / Jinja** | Web UI va xavfsiz HTML shablonlar. |
| **pytest** | 102 avtomatik test. Har o'zgarishdan keyin kod buzilmaganini bir buyruq bilan tekshiramiz. |
| **Playwright + Chromium** | UI'ni **haqiqiy brauzerda** sinash: suratga olish, tugmalarni bosish, xatolarni ko'rish. |
| **gunicorn, Docker, Render** | Internetga joylash. |
| **git / GitHub** | Versiyalarni saqlash; Render shu yerdan oladi. |
| **IDA Free / Ghidra** | Haqiqiy foydalanishda psevdokod manbasi (eksport skriptlari yozilgan). |

**Nega testlar bunchalik muhim?** Loyiha katta (~6000 qator). Bitta joyni tuzatganda boshqa joy buzilishi mumkin. Testlar
buni darrov ko'rsatadi. Audit topgan har bir xato uchun **alohida regressiya testi** yozdik: xato qaytib kelmasligi uchun.

---

## 9. Xatolar va saboqlar (halol hisobot)

Oxirgi bosqichda siz "ishni boshidan tahlil qil, xato ketgan joying bormi?" dedingiz. Biz **5 ta mustaqil tekshiruvchi**
yaratdik: ular kodga tegmaydi, faqat uni **yangi kirishlar bilan "hujum" qilib** sinaydi va har bir topilma uchun aniq misol
keltiradi. Ularning da'volarini ko'r-ko'rona qabul qilmadik: eng og'irlarini qayta ishga tushirib tasdiqladik.

### 9.1. Eng muhim saboq

> Oldingi bosqichlarda "**Tasdiqlandi**" deganimiz ba'zi hollarda **yolg'on ishonch** bergan.

Tasodifiy test kuchli, lekin cheksiz emas. Biz test **nimani topa olmasligini** o'rganishimiz kerak edi.

### 9.2. Topilgan jiddiy xatolar

| Xato | Nima bo'lgan | Qanday tuzatdik |
|---|---|---|
| **Haqiqiy mantiq o'chirilgan** | `if (a1 == 1337 && a2 == 31337 && a3 == 42)` "soxta shart" deb o'chirilgan, natija esa «Tasdiqlandi». Chunki tasodifiy sinov bunday shartni hech qachon uchratmaydi. | Taqqoslanayotgan qiymat ko'p turli qiymat olsa, shart "doimiy" hisoblanmaydi. Test esa parametrlarga koddagi literallarni **ketma-ket** beradi. |
| **Test zaif edi** | Bufer bilan birga kelgan butun sonlar faqat 0..512 edi — manfiy va katta qiymatlar umuman sinalmagan. | Har to'rtinchi qiymat istalgan; buferlar qo'riqchi sahifa bilan o'ralgan. |
| **Osilgan/qulagan kod o'tib ketgan** | Yangi kod cheksiz tsiklga tushsa yoki qulasa, natija `compiled` (yaxshi) deb hisoblangan. | Endi bu `mismatch`. Stek to'lishi ham ushlanadi. |
| **Jadvaldagi xato yashirinib qolgan** | Yangi kod jadvalni boshqa qiymat bilan yozsa, vosita uni asl nusxa bilan almashtirib yuborgan. | Boshqa qiymatli jadval yangi kodning o'z nusxasi bo'lib qoladi — farq ko'rinadi. |
| **Soxta natija** | Tekshirilayotgan kod `RESULT ...` satrini o'zi chop etib, testni aldab o'tishi mumkin edi. | Natija satrlariga tasodifiy so'z (nonce) qo'shildi. |
| **Imzo turi tekshirilmagan** | `int` o'rniga `short` yoki `void` qaytaradigan kod "tasdiqlangan". | Tur kengligi va void/ko'rsatkich farqi tekshiriladi. |
| **Soddalashtirish turni o'zgartirgan** | `(unsigned short)(...)` o'rniga oddiy `c` yozilgan: natija boshqa. | Tur saqlanadi yoki cast qo'shiladi; bo'lmasa o'zgartirilmaydi. |
| **Yon ta'sir yo'qolgan** | `i++` va funksiya chaqiruvi "sof qiymat" deb o'chirilgan. | Yon ta'sirli ifodalar tegilmaydi. |
| **Matn literallari buzilgan** | Kod boshidagi `"hello world"` bo'sh joylarga aylangan. | Aslidek ko'chiriladi. |
| **`else` muammosi** | Keraksiz qator o'chirilganda yolg'iz `else` keyingi gapni "yutgan". | `else` ham olib tashlanadi. |
| **Claude javobi kesilsa agent to'xtagan** | Xom pydantic xatosi chiqib, offline zaxira ishlamagan va sarf hisobga olinmagan. | Endi tushunarli xato + zaxira + narx hisoblanadi. |
| **Yordamchi funksiya nomi** | Claude `rotl32` ni `rotate_left` deb chaqirsa, test `mismatch` bergan. | Asl nom saqlanishi prompt va eslatmada aniq aytilgan. |
| **Public demo: begona kod serverda ishga tushgan** | Eng xavflisi. Sandbox haqiqiy izolyatsiya emas edi. | Public rejimda kod **ishga tushirilmaydi** (11-bo'lim). |
| **Public: kalit "oracle"i** | `/api/check-key` server kaliti bilan ishlagan va cheklanmagan. | Public rejimda server kaliti ishlatilmaydi + cheklov. |
| **Tezlik cheklovi xatosi** | 4097-chi turli IP'dan keyin sayt 500 xatosi bera boshlagan. | Tuzatildi. |
| **`Dockerfile`** | `wsgi.py` nusxalanmagan — konteyner ishga tushmas edi (**men yozgan edim**). | Tuzatildi va toza muhitda sinab ko'rildi. |
| **CSRF himoyasi o'zi xato** | Birinchi variantim oddiy foydalanuvchi formasini ham 403 bilan rad etardi. | Faqat **haqiqiy brauzerda** topildi; `Referrer-Policy: same-origin` qilindi. |
| **Sekinlik** | Yangi `narrate.py` uzun kodda ifodani eksponensial kattalashtirib, 200 s+ va 1 GB xotira yeyardi. | Ifoda o'lchami 120 tugun bilan cheklandi. |

### 9.3. Nega buni yashirmaymiz?

Ilmiy va muhandislik ishida **o'z xatolarini topish va tuzatish** — kamchilik emas, balki ishning sifat belgisi. Ustoz
"nega ishonaman?" desa, javob: "chunki biz uni *sindirishga* urindik va topilgan har bir xato uchun test yozdik".

---

## 10. Natijalar va ularni qanday o'qish kerak

### 10.1. 8 ta namuna bo'yicha (offline rejim)

| Ko'rsatkich | Natija | Nima degani |
|---|---|---|
| Psevdokodga ekvivalent (gcc + differensial test) | **8 / 8** | Vosita chiqargan kod kirishdagi psevdokod bilan bir xil ishlaydi. |
| Haqiqiy asl (toza) kodga ekvivalent | **6 / 8** | 2 tasida dekompilyator (angr) **o'zi** xato qilgan: `% 2` amalini tushirib qoldirgan. Bu vositaning emas, dekompilyatorning xatosi. |
| Chalkashtirish usullarini topish | **100%** | Har bir namunadagi usul aniqlangan. |
| Tsiklomatik murakkablik | **58 → 21** (−64%) | Shartlar va tsikllar soni kamaydi: kod soddalashdi. |
| Qatorlar | **216 → 95** (−56%) | Kod qisqardi. |

**Tsiklomatik murakkablik** — koddagi "yo'l ayrilishlari" soni (`if`, `while`, `case` + 1). Son qancha katta bo'lsa, kodni
tushunish shuncha qiyin.

### 10.2. 21 ta realistik kirish (IDA/Ghidra uslubida yozilgan)

61 ta funksiya: **50 tasi tasdiqlandi**, **6 tasi** `compiled` (avtomatik solishtirib bo'lmadi: funksiya ko'rsatkichi
parametri kabi), **5 tasi** `compile_error` (C++ nomlari `Crypto::mix`, Ghidra'ning ba'zi `CONCAT` shakllari, IDA'ning
`start` kabi boshlang'ich funksiyalari — avvaldan ma'lum cheklovlar). **Noto'g'ri natija (mismatch) — 0.**

### 10.3. Testlar

**102 / 102** avtomatik test o'tadi (`python -m pytest`). Ular: parser, detektorlar, tekislash, Claude moduli (soxta
mijoz bilan), agent, differensial test (audit topgan holatlar bilan), tushuntirish sifati, Web UI va xavfsizlik, audit
regressiyalari.

### 10.4. Claude Sonnet 5.5 — haqiqiy API bilan o'lchov

Kalit bilan lokalda 5 funksiya tahlil qilindi (to'liq jadval: `docs/baholash_claude_sonnet.md`):

| Funksiya | Natija | Narx | Vaqt | Claude bergan nom |
|---|---|---|---|---|
| `gcd` | Tasdiqlandi, 1-urinishda | $0.0345 | 23 s | `gcd` |
| `checksum` | Tasdiqlandi, 1-urinishda | $0.0392 | 24 s | `fnv1a_checksum` |
| `rotl32` | Tasdiqlandi, 1-urinishda | $0.0256 | 15 s | `rotate_left_32` |
| `rot_hash` | Tasdiqlandi, 1-urinishda | $0.0346 | 20 s | `rot_hash` |
| `bubble_sort` (Web UI) | Tasdiqlandi (1690 test), 1-urinishda | $0.0243 | 24 s | `bubble_sort` |

O'rtacha ≈ $0.032 / funksiya. **Ma'nosi:** offline (qoidalar) va Claude bir xil natijaga — tasdiqlangan toza kodga — keldi,
lekin Claude mazmunli nom beradi va tushuntirishni funksiyaga moslab yozadi. **Cheklov:** tanlama kichik; xato tuzatish
sikli (hamma natija 1-urinishda to'g'ri chiqdi) va zararli kodda rad etish haqiqiy Claude bilan ko'rilmagan.

### 10.5. Brauzer sinovi

UI Chromium'da kompyuter (1280 px) va telefon (390 px) o'lchamida tekshirildi: forma yuboriladi, "Oddiy tilda" tugmasi
ishlaydi, kod ranglanadi, gorizontal skroll yo'q, konsolda xato yo'q.

---

## 11. Xavfsizlik: har bir himoya nima uchun

### 11.1. Muammoning mohiyati

Vosita **kodni ishga tushiradi** (differensial test uchun). O'z kompyuteringizda bu xavfsiz: kodni o'zingiz berasiz.
**Internetda esa kodni begona odam beradi.** Agar server uning kodini ishga tushirsa, u serverdagi fayllarni o'qishi,
boshqa foydalanuvchilarning kalitlariga tegishi yoki serverni ishdan chiqarishi mumkin.

### 11.2. Qaror: public rejimda kod ishga tushirilmaydi

Birinchi variantda cheklovlar (vaqt, xotira, jarayonlar soni) bilan "sandbox" yasagan edik. Audit **bu haqiqiy izolyatsiya
emasligini** ko'rsatdi: cheklovlar *resursni* chegaralaydi, lekin dasturni boshqa narsalardan *ajratmaydi*. Shuning uchun:

* **Public rejimda** (`DEOBF_PUBLIC=1`) gcc ham, test ham **ishga tushirilmaydi**. Natija halol: «**Tekshirilmadi**».
* Offline natijadagi har bir soddalashtirish baribir Python ichida **hisoblab** tekshiriladi (kodni ishga tushirmasdan) —
  lekin bu *butun funksiya* bo'yicha tekshiruv emas.
* To'liq tekshiruv (gcc + differensial test) — **o'z kompyuteringizda**.
* Operator `DEOBF_NATIVE=1` bilan yoqishi mumkin, lekin **faqat** alohida izolyatsiyalangan muhitda (gVisor/Firecracker
  kabi, tarmoqsiz, maxfiy qiymatsiz). Oddiy Docker konteyneri yetarli emas.

### 11.3. Boshqa himoyalar

| Himoya | Nimadan | Qanday |
|---|---|---|
| **BYOK** (kalit saqlanmaydi) | Begonalar sizning pulingizni sarflashidan | Server kalit saqlamaydi; foydalanuvchi o'z kalitini kiritadi; kalit sahifaga qaytarilmaydi va jurnalga yozilmaydi. |
| **Kalit formati tekshiruvi** | Noto'g'ri/zararli qiymat | `sk-ant-` + kamida 20 belgi. |
| **Cheklovlar** | Serverni ishdan chiqarish (DoS) | Kirish ≤ 20 000 belgi, ≤ 3 funksiya, 90 s umumiy vaqt, bir vaqtda 2 tahlil (`503`), 10 daqiqada 15 tahlil (`429`). |
| **Kalit tekshiruvi cheklovi** | Server orqali boshqa kalitlarni sinab ko'rish | 10 daqiqada 6 ta. |
| **Origin / Sec-Fetch-Site (CSRF)** | Boshqa sayt sizning nomingizdan so'rov yuborishi | Mos kelmasa — `403`. |
| **Host tekshiruvi** (shaxsiy rejim) | DNS rebinding: boshqa sayt `localhost` dagi vositangizga murojaat qilishi | Faqat `127.0.0.1`/`localhost`. Aks holda boshqa sayt sizning kompyuteringizda kod ishga tushirishi mumkin edi. |
| **Qat'iy CSP** | XSS | `script-src 'self'`; `highlight.js` loyihaning o'zidan (CDN yo'q). |
| **Ekranlash** | XSS | Model va foydalanuvchi matni doim ekranlanadi; `|safe` hech qayerda yo'q. |
| **Root bo'lmagan foydalanuvchi** | Konteyner buzilsa zarar kengayishi | Konteynerda dastur UID 10001 nomidan ishlaydi. |
| **Aniq versiyalar** | "Kecha ishlagandi, bugun yo'q" | `gunicorn==23.0.0`, kutubxonalarning major versiyalari qotirilgan. |

---

### 11.4. Yopiq demo: nega endi kod ishga tushadi va loyiha to'liq ishlaydi

**Savol, ko'pchilik so'raydi:** "11.2 da kod ishga tushmaydi, natija «Tekshirilmadi» dedingiz. Loyiha ishlamasa, u nima
uchun kerak?"

**Javob — vaziyatga bog'liq:**

* Havolani **hamma** ochishi mumkin bo'lsa (ochiq demo), begona odam zararli kod yuborishi mumkin. Shuning uchun u yerda
  tekshiruv o'chirilgan: bu *xavfsizlik uchun to'langan narx*.
* Havolani faqat **siz va ustoz** ishlatsangiz, vaziyat boshqa: kodni faqat **kirish kodini bilganlar** yuboradi. Shuning
  uchun **yopiq demo** yaratdik: kirish kodi bilan kirgach, hamma narsa **to'liq** ishlaydi — Claude (sizning kalitingiz bilan),
  gcc kompilyatsiyasi va differensial test, «Tasdiqlandi» natijasi.

**Yopiq demo qanday himoyalanadi** (har bir qatlam va uning sababi):

| Qatlam | Nima | Nega |
|---|---|---|
| **Kirish kodi** (`DEOBF_ACCESS_CODE`) | Saytning hamma sahifasi (hatto natijalarni yuklab olish ham) kodsiz yopiq. | Begonalar kod yubora olmasin va kalitingizdan foydalana olmasin. |
| **Urinishlar cheklovi** | Noto'g'ri kod: bitta IP'dan 15 daqiqada 5 ta, jami 1 soatda 40 ta; undan keyin bloklanadi. | 4 xonali kod — 10 000 variant. Cheklovsiz uni bir necha daqiqada terib topish mumkin edi. |
| **Kunlik byudjet** (`DEOBF_DAILY_BUDGET_USD`) | Kuniga Claude uchun ko'pi bilan shuncha dollar; keyin Claude to'xtaydi, offline ishlayveradi. | Kod qo'lga tushsa ham, pulingiz cheksiz ketmaydi. |
| **Alohida foydalanuvchi** (`DEOBF_SANDBOX_UID`) | Server `root`, tekshirilayotgan kod esa huquqsiz `sandbox` foydalanuvchisi nomidan ishlaydi. | Kod serverning muhit o'zgaruvchilarini o'qiy olmaydi, ya'ni **API kalit o'g'irlanmaydi**. Bu tekshirilgan: `Permission denied`. |
| **O'z-o'zini sinash** | Server ishga tushganda ajratish ishlashi sinab ko'riladi; ishlamasa, kod ishga tushirilmaydi. | Himoya jimgina buzilib qolmasligi uchun. |
| **Xavfsiz sozlama majburiyati** | `DEOBF_USE_SERVER_KEY` kirish kodisiz yoqilsa, server ishga tushmaydi. | Adashib kalitni hammaga ochib qo'ymaslik uchun. |
| **Maxfiy qiymatlar repoda yo'q** | Kod va kalit faqat Render sozlamalarida. | GitHub'ni boshqalar ko'rishi mumkin. |

**Qoldiq xavf (halol):** 4 xonali kod — kuchsiz parol. Cheklovlar uni topishni sekinlashtiradi, lekin imkonsiz qilmaydi.
Kodni topgan odam sizning kalitingiz bilan (byudjet chegarasida) Claude'dan foydalanishi va kodini serverda
(huquqsiz foydalanuvchi nomidan) ishga tushirishi mumkin. Shuning uchun: (1) Anthropic konsolida **oylik limit** qo'ying;
(2) ustozga ko'rsatgach, kodni o'zgartiring yoki xizmatni to'xtating.

---

## 12. Internetga chiqarish

### 12.1. Hozirgi holat — halol

* **Tayyor:** `Dockerfile`, `render.yaml`, `wsgi.py`, yo'riqnoma (`docs/04_internetga_chiqarish.md`).
* **Qanday sinalgan:** haqiqiy Chromium'da xuddi Render'dagi sozlamalar bilan: kodsiz kirsa `/login` ga o'tadi; noto'g'ri
  kod rad etiladi; to'g'ri kod bilan kiriladi; offline tahlil **«Tasdiqlandi. 2000 ta tasodifiy test»** (kod alohida
  foydalanuvchi nomidan ishga tushirilgan); Claude so'rovi (soxta kalit bilan) Anthropic serveriga yetib borib, tushunarli
  «Kalit noto'g'ri» xabari qaytardi. Ajratishning o'zi ham sinalgan: bola jarayon `uid=10002`, serverning muhitini
  o'qimoqchi bo'lganda `Permission denied`.
* **Joylanmagan:** Render'da hisob ochib «Create» bosish **faqat siz** qila oladigan ish: bu muhitda hech qanday bulut
  hisobi ulanmagan. Haqiqiy `docker build` ham bu yerda ishga tushirilmagan (Docker yo'q).

### 12.2. Qadamlar (Render, bepul)

1. Anthropic konsolida kalit yarating va **oylik xarajat limiti** qo'ying (docs/04, 3.1).
2. [render.com](https://render.com) ga GitHub bilan kiring → **New → Blueprint** → `Uchqunbek12/for-claude-work`.
   GitHub'dagi asosiy branch aynan bizning branchimiz, shuning uchun Render uni o'zi oladi.
3. Render **ikkita qiymat** so'raydi: `DEOBF_ACCESS_CODE` (kirish kodi) va `ANTHROPIC_API_KEY` (Claude kaliti). Ularni
   **faqat shu yerga** kiriting (chatga yoki GitHub'ga emas). Qolgan sozlamalar (server kaliti, to'liq tekshiruv) kirish kodi
   bo'lgani uchun **avtomatik** yoqiladi. Sayt nomini `DEOBF_SITE_NAME` bilan, havola nomini Render → Settings → Name bilan o'zgartirasiz.
4. **Apply** bosing, 3–6 daqiqa kuting. Render `https://deobf-agent-xxxx.onrender.com` havolasini beradi.
5. Havolani ochsangiz, **kirish kodi** so'raladi. Kod bilan kirgach, hammasi ishlaydi.
6. Bepul reja 15 daqiqa ishlatilmasa uxlab qoladi (birinchi ochilish 30–60 s sekinroq): namoyishdan oldin bir marta oching.

### 12.3. Nega aynan shu tanlovlar

| Tanlov | Sabab |
|---|---|
| Docker | Qayerda ochilsa ham bir xil ishlaydi; gcc ichida bor. |
| `--workers 1 --threads 8` | Hisobotlar va cheklovlar jarayon xotirasida; ko'p jarayonda yuklab olish havolasi tasodifiy «topilmadi» bo'lardi. |
| `exec gunicorn` | O'chirishda signal to'g'ri yetib borishi uchun. |
| `/healthz` | Render sog'liq tekshiruvi kirish kodisiz ishlashi uchun. |
| `DEOBF_TRUSTED_PROXIES=1` | Render proksi orqasida: urinish cheklovi har bir **haqiqiy** mijoz uchun alohida bo'lishi uchun. |
| `sync: false` | Maxfiy qiymatni Render sizdan so'raydi va GitHub'ga yozilmaydi. |

---

## 13. API ishlayaptimi? Kalit haqida

**Hozirgi holat:** bu muhitda (men ishlayotgan joyda) haqiqiy kalit **yo'q**, shuning uchun Claude'ning *haqiqiy javobini*
ko'rmaganman. Lekin API yo'li ochiq ekani tasdiqlandi: soxta kalit bilan so'rov Anthropic serveriga yetib bordi va server
«kalit noto'g'ri» deb javob berdi, vosita buni tushunarli xabarga aylantirdi.

| Savol | Javob |
|---|---|
| Kalit qo'yilganmi? | **Yo'q** — kalit faqat sizda. Uni Render'ga **siz** kiritasiz (12.2, 3-qadam). Men uni ko'ra ham, yozib ham olmayman, GitHub'ga ham tushmaydi. |
| Nega kalitni menga yubormang? | Kalit — parol: u orqali sizning pulingiz sarflanadi. Chat yozuvlari saqlanadi. Maxfiy qiymat faqat Render'ning maxfiy sozlamasida turishi kerak. |
| Claude rejimi sinalganmi? | **Ha, lokalda haqiqiy kalit bilan**: 5 funksiya, hammasi 1-urinishda «Tasdiqlandi», narx $0.024–0.039 (10.4-bo'lim). Render ustida hali ishlatilmagan. |
| Offline rejim kalit kerakmi? | Yo'q. Bepul va kalitsiz ishlaydi. |

### Kalitni tekshirish

* Saytda **«Kalitni tekshirish»** tugmasi: `models.retrieve` ni chaqiradi — u matn yaratmaydi, shuning uchun **bepul**.
* O'z kompyuteringizda: `2_kalit_kiritish.bat` (kalitni to'g'ri yozadi va darhol tekshiradi), keyin `4_tekshirish.bat` yoki `deobf check`.
* Render'da kalit noto'g'ri bo'lsa, tahlil natijasida «Kalit noto'g'ri yoki bekor qilingan» xabari chiqadi va offline natija ko'rsatiladi.

## 14. Cheklovlar: nima ishlamaydi

Quyidagilar **hujjatlarda ochiq aytilgan** va ustoz so'rasa, yashirmasdan javob bera olasiz:

| Cheklov | Ma'nosi |
|---|---|
| Tasodifiy test — isbot emas | "Tasdiqlandi" = 2000 tasodifiy kirishda mos keldi. Matematik isbot (SMT/Z3) emas. |
| Test ko'rmaydigan narsalar | `NULL` ko'rsatkich, ikki ko'rsatkichning ustma-ust tushishi, funksiyaning ekranga chiqargan matni, `x == (1<<20)` kabi hosila konstantalar. |
| Murakkab tekislash | Ichma-ich `switch`, `while (st != 9)` shakli yechilmaydi (kod xavfsiz tarzda tegmasdan qoladi). |
| Chaqiruv argumenti ichidagi MBA | `f((a^b)+2*(a&b))` ichidagi ifoda soddalashtirilmaydi. |
| C++ nomlari, ba'zi Ghidra `CONCAT` | Kompilyatsiya bo'lmaydi. |
| Virtualizatsiya (VMProtect) | Loyiha doirasidan tashqarida. |
| **Claude rejimi kichik tanlamada sinalgan** | 5 funksiya, 4 namuna. Xato tuzatish sikli va zararli kodda rad etish haqiqiy Claude bilan ko'rilmagan. |
| **`docker build` ishga tushirilmagan** | Qadamlar qayta ishlab ko'rilgan, haqiqiy build emas. |
| Ochiq demo (kodsiz) kodni ishga tushirmaydi | Xavfsizlik uchun «Tekshirilmadi». To'liq tekshiruv — yopiq demoda (kirish kodi bilan) yoki lokal. |
| 4 xonali kirish kodi kuchsiz | Cheklovlar va byudjet bilan himoyalangan, lekin imkonsiz emas: uzunroq kod qo'yish va Anthropic'da oylik limit belgilash tavsiya etiladi. |
| Yopiq demoda kod serverda ishga tushadi | Huquqsiz foydalanuvchi nomidan, lekin tarmoq va umumiy yadro izolyatsiyasi (gVisor/VM kabi) yo'q: faqat ishonchli kishilarga kod bering. |
| Dekompilyator xatolari | angr ba'zan o'zi xato qiladi (2/8 namuna); vosita psevdokodni etalon deb oladi. |

---

## 15. Ustozga namoyish rejasi (5–7 daqiqa)

Namoyishdan oldin ikki yo'ldan birini tanlang:

* **Internetdagi sayt (Render):** havolani **oldindan bir marta oching** (bepul reja uxlab qoladi, birinchi ochilish
  30–60 s), kirish kodini kiriting. Ustozga havolani va kodni alohida xabarda yuboring.
* **Kompyuteringizda:** terminalda `.venv` faol bo'lsin (yoki `3_web_ishga_tushirish.bat`), `deobf web`.

1. **Muammoni ko'rsating (1 daqiqa).** `samples/decompiled/s5_combined.angr.c` ni oching: 49 qator, `while(1){switch}`,
   ma'nosiz nomlar. "Mana shuni tushunish qiyin."
2. **Web UI (2 daqiqa).** `deobf web` → "Namuna: s5_combined" → Model: **Offline** → "Tahlil qilish". Ko'rsating:
   * chapda asl, o'ngda soddalashtirilgan kod (49 → 20 qator);
   * **"Tasdiqlandi. 2000 ta tasodifiy test — barchasi mos keldi"**;
   * xulosa: "FNV-1a xesh hisoblaydi";
   * **"Oddiy tilda"** tugmasini bosing — hamma matn dehqoncha bo'ladi.
3. **Tekshiruv nima ekanini ayting (1 daqiqa).** "Biz kodni gcc bilan kompilyatsiya qilib, asl kod bilan 2000 marta
   solishtiramiz. Bu isbot emas, lekin kuchli dalil."
4. **Raqamlar (1 daqiqa).** `docs/baholash_offline.md`: 8/8, murakkablik 58→21.
5. **Testlar (30 s).** `python -m pytest -q` → **102 passed**.
6. **Halollik (1 daqiqa).** "Biz kodni mustaqil tekshiruvchilar bilan sindirdik: 18 ta jiddiy xato topildi (ba'zilari bizning 'tasdiqlandi'mizni
   noto'g'ri qilib qo'yardi) va hammasi tuzatildi, har biri uchun test yozildi (9-bo'lim)." — bu ustozga eng yaxshi taassurot qoldiradi.
7. **Claude (kalit ulangan bo'lsa).** Yopiq saytda server kaliti bilan, kompyuteringizda `.env` dagi kalit bilan. Model: Sonnet → bir
   funksiya → "mazmunli nom va izoh qanday chiqdi". Kalit bo'lmasa yoki xato bo'lsa, sayt tushunarli xabar beradi va offline natijani ko'rsatadi.

---

## 16. Ustoz berishi mumkin bo'lgan savollar va javoblar

**1. Nega LLM kerak, agar qoidalar bilan ham soddalashtirsa bo'ladi?**
Qoidalar faqat *oldindan biladigan* shakllarni yecha oladi. LLM yangi, noma'lum shaklni tushunadi, o'zgaruvchilarga mazmunli
nom beradi va tabiiy tilda tushuntiradi. Shuning uchun ikkalasini birlashtirdik: qoidalar — ishonchli va bepul asos; LLM —
moslashuvchan "aql".

**2. LLM xato qilsa-chi?**
Aynan shuning uchun tekshiruv bor: LLM javobi kompilyatsiya qilinadi va asl kod bilan minglab tasodifiy kirishda
solishtiriladi. Xato bo'lsa, farq LLM'ga qaytariladi (3 marta). Baribir bo'lmasa, tasdiqlangan offline natija olinadi.

**3. "Ekvivalent" ekanini qanday bilasiz?**
Matematik isbotlay olmaymiz. Differensial test minglab tasodifiy va chegaraviy kirishda bir xil natijani ko'rsatadi — bu
kuchli *dalil*, lekin isbot emas (14-bo'lim). Shuning uchun hisobotda "Tasdiqlandi" deymiz, "isbotlandi" demaymiz.

**4. Nega ba'zi natijalar "Tekshirilmadi"?**
Faqat **ochiq** demoda (parolsiz, hamma kira oladigan): u yerda begona kodni serverda ishga tushirish xavfli, shuning uchun
tekshiruv o'chirilgan. **Yopiq** demoda (kirish kodi bilan) va kompyuteringizda to'liq tekshiruv ishlaydi — «Tasdiqlandi»
chiqadi. Ya'ni loyiha to'liq ishlaydi; xavfsizlik darajasini kimga ochilganiga qarab tanlaymiz (11.4).

**5. Nega standart model Sonnet, Haiku emas?**
Sifat va narx o'rtasidagi muvozanat: Sonnet kuchliroq, Haiku ~20 baravar arzon. Ikkalasi bir tugma bilan almashtiriladi.

**6. Narx qancha?**
≈ $0.03 / funksiya (Sonnet): 5 ta funksiyada haqiqiy API bilan o'lchangan $0.024–0.039. Haiku ~20 baravar arzon. Offline — bepul.

**7. Obfuskatsiyaning qaysi turlari yechiladi?**
MBA, soxta shart, oddiy tekislash, kodlangan satr/konstanta, o'lik kod. Virtualizatsiya (VMProtect) — yo'q.

**8. Nega "agent" deysiz?**
Chunki u natijasini o'zi tekshiradi va xato bo'lsa harakatini o'zgartiradi (xatoni modelga qaytaradi, zaxiraga o'tadi).

**9. Xavfsizlik haqida nima qildingiz?**
Public rejimda kod ishga tushirilmaydi; kalit saqlanmaydi (BYOK); kirish/tezlik cheklovlari; CSRF/DNS rebinding himoyasi;
qat'iy CSP; ekranlash; root bo'lmagan foydalanuvchi (11-bo'lim).

**10. Eng katta xatongiz nima edi?**
"Tasdiqlandi" degan natijamiz ba'zi hollarda yolg'on bo'lgan: masalan, haqiqiy shartni "soxta" deb o'chirib yuborgan.
Mustaqil tekshiruvchilar topdi, biz tuzatdik va har biri uchun test yozdik (9-bo'lim).

**11. Nega testlarni brauzerda ham o'tkazdingiz?**
Birlik testlar test mijozi bilan ishlaydi; haqiqiy brauzer boshqacha so'rov yuboradi. Aynan shu yo'l bilan o'zimiz kiritgan CSRF
xatoni topdik.

**12. Boshqa dasturchi bu loyihani qanday davom ettiradi?**
`docs/` papkasida hamma narsa yozilgan: yo'riqnoma (02), jurnal (01), hisobot (03), joylash (04), dehqoncha (05) va shu hujjat.
102 test o'zgarishlarni himoya qiladi.

**13. IDA va Ghidra bilan qanday ishlaydi?**
Ikki yo'l: psevdokodni nusxalab joylash (IDA Free'da `F5 → Ctrl+A → Ctrl+C`) yoki eksport skriptlari (`scripts/ida_export.py`,
`scripts/ghidra_export.java`). Parser uslubni o'zi aniqlaydi. *Eslatma:* eksport skriptlari IDA/Ghidra o'rnatilgan
kompyuterda hali sinalmagan.

**14. Nima uchun test namunalarini o'zingiz yaratdingiz?**
"To'g'ri javob"ni bilish uchun: toza kodni yozib, uni chalkashtirdik, kompilyatsiya qilib dekompilyatsiya qildik. Shunda
vosita natijasini toza kod bilan **haqiqatan** solishtira olamiz (6/8).

**15. Nega 2 tasi 6/8 da emas?**
Dekompilyator (angr) o'zi xato qilgan (`% 2` amalini tushirib qoldirgan). Vosita psevdokodni etalon deb oladi, shuning uchun
natija psevdokodga ekvivalent, lekin asl kodga emas. Bu dekompilyator xatosi.

---

## 17. Nazariy qism uchun nima qoldi

Amaliy qism tugadi. Nazariy qismda quyidagilarni yozish mumkin (hammasi bu hujjatda va `docs/00` da asos bor):

* obfuskatsiya turlari va ularning tarixi/maqsadi (2.2-bo'lim);
* deobfuskatsiya usullari: statik tahlil, simvolik bajarish, SMT-yechuvchilar (Z3), LLM yondashuvi;
* LLM'ning kuchli va zaif tomonlari (xato qilishi, "gallyutsinatsiya") va nega **tekshiruv** kerakligi;
* differensial test va uning chegaralari (isbot emas, dalil);
* xavfsizlik: nega begona kodni ishga tushirmaslik kerak;
* mavjud vositalar bilan solishtirish (masalan, mavjud deobfuskatorlar, simvolik bajarish asosidagi vositalar).

*Qo'shimcha manbalar:* `docs/00_mavzu_tushuntirish.md` (mavzu va reja), `docs/01_jurnal.md` (har bir qadam va nega),
`docs/03_amaliy_qism_hisoboti.md` (rasmiy hisobot), `docs/baholash_offline.md` (natija jadvali).
