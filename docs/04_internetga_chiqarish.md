# 04. Internetga chiqarish (deploy)

Bu yo'riqnoma vositani internetga — hamma kira oladigan manzilga — qanday qo'yishni tushuntiradi.
Maqsad: siz havolani (masalan `https://deobf-agent.onrender.com`) ulashasiz, boshqalar brauzerda ochib
sinab ko'radi.

> **Eng muhim qoida.** Internetdagi serverga **o'z API kalitingizni QO'YMANG.** Agar qo'ysangiz,
> har bir begona odam sizning hisobingiz hisobidan Claude'ga so'rov yuboradi — pulini siz to'laysiz.
> Shuning uchun vositada **public rejim** bor: server kalit saqlamaydi.

---

## 1. Ikki rejim farqi

| | Shaxsiy rejim (kompyuteringizda) | Public rejim (internetda) |
|---|---|---|
| Kim ishlatadi | faqat siz | hamma |
| API kalit | `.env` dagi sizning kalitingiz | **server kalit saqlamaydi**; Claude kerak bo'lsa, tashrif buyuruvchi O'Z kalitini kiritadi (u hech qayerda yozilmaydi) |
| Standart dvigatel | Haiku (Claude) | **Offline** (bepul, LLM'siz) |
| Cheklovlar | yumshoq | qattiq: kirish ≤ 20 000 belgi, 10 daqiqada 15 so'rov, disk kesh o'chirilgan |
| Xavfsizlik sarlavhalari | yo'q | bor (CSP, X-Frame-Options va h.k.) |

Public rejim `DEOBF_PUBLIC=1` muhit o'zgaruvchisi bilan yoqiladi. Hamma cheklov `deobf_agent/web/app.py`
va `deobf_agent/sandbox.py` ichida.

---

## 2. Xavfsizlik: nega buni internetga qo'yish xavfsiz?

Vosita begona odam bergan kodni **kompilyatsiya qiladi va ishga tushiradi** (differensial test uchun).
Bu — eng nozik joy. Shuning uchun bir necha himoya qatlami bor:

1. **Kalit saqlanmaydi.** Serverda hech qanday maxfiy kalit yo'q. Claude modeli uchun tashrif buyuruvchi
   o'z kalitini kiritadi; u faqat o'sha bitta so'rov uchun ishlatiladi va hech qayerda yozilmaydi.
2. **Tozalangan muhit** (`sandbox.clean_env`): ishga tushirilgan `gcc` va test dasturiga faqat `PATH`,
   `LANG` kabi zarur o'zgaruvchilar beriladi — hech qanday kalit yoki maxfiy qiymat uzatilmaydi.
3. **Resurs chegaralari** (`sandbox._limits`): protsessor vaqti, xotira, yoziladigan fayl hajmi
   cheklanadi; public rejimda jarayonlar va ochiq fayllar soni ham. Vaqt tugasa — butun jarayonlar guruhi
   to'xtatiladi (cheksiz tsikl yoki «vilka bombasi» serverni osib qo'ymaydi).
4. **`#include` taqiqlangan** (public rejimda): tashrif buyuruvchi faqat funksiyaning o'zini joylaydi.
5. **Root bo'lmagan foydalanuvchi:** konteynerda server oddiy foydalanuvchi (`deobf`, UID 10001) nomidan
   ishlaydi — konteyner buzilsa ham zarar cheklangan.
6. **Xavfsizlik sarlavhalari** (CSP, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`).

> Shunga qaramay, bu o'quv loyihasi. Haqiqiy ishlab chiqarishda konteyner yana bir qavat izolyatsiyada
> (masalan, alohida tarmoqsiz muhit) ishlashi kerak. Bepul xosting demo uchun yetarli.

---

## 3. Eng oson yo'l: Render.com (bepul, Docker)

Render — bepul rejasi bor xosting. Repozitoriyadagi `Dockerfile` va `render.yaml` tayyor.

1. Kodingizni GitHub'ga joylang (bu repozitoriya allaqachon GitHub'da).
2. [render.com](https://render.com) da ro'yxatdan o'ting, GitHub hisobingizni ulang.
3. **New → Blueprint** tanlang va shu repozitoriyani ko'rsating. Render `render.yaml` ni o'qib,
   `DEOBF_PUBLIC=1` bilan Docker servisini o'zi yaratadi.
4. **Create** bosing. Birinchi qurilish (build) 3–5 daqiqa davom etadi.
5. Tayyor bo'lgach, Render sizga `https://<nom>.onrender.com` havolasini beradi. Shuni ulashing.

Nozik jihatlar:
- **Bepul reja «uxlab qoladi».** 15 daqiqa foydalanilmasa server to'xtaydi; keyingi ochilish 30–60 soniya
  sekinroq bo'ladi (server qayta uyg'onadi). Demo uchun bu normal.
- **gcc konteynerda bor** (`Dockerfile` o'rnatadi), shuning uchun differensial test internetda ham ishlaydi.

---

## 4. O'zingiz sinab ko'rish (Docker'siz)

Internetga qo'yishdan oldin public rejimni o'z kompyuteringizda sinab ko'ring:

```bash
deobf web --public
```

Brauzerda `http://127.0.0.1:5000` ochiladi, lekin endi public rejim ko'rinishida: standart dvigatel —
Offline, Claude uchun kalit maydoni bor, cheklovlar yoqilgan. `Ctrl+C` bilan to'xtatiladi.

Docker bilan sinash (agar Docker o'rnatilgan bo'lsa):

```bash
docker build -t deobf-agent .
docker run -p 8000:8000 deobf-agent
# brauzerda http://127.0.0.1:8000
```

---

## 5. Boshqa xostinglar

`Dockerfile` oddiy, shuning uchun Docker qabul qiladigan har qanday xostingda ishlaydi
(Fly.io, Railway, o'z VPS'ingiz va h.k.). Faqat ikki narsani ta'minlang:

- `DEOBF_PUBLIC=1` muhit o'zgaruvchisi o'rnatilgan bo'lsin;
- konteynerda `gcc` bo'lsin (bizning `Dockerfile` da bor). gcc bo'lmasa vosita baribir ishlaydi, lekin
  natijalarni avtomatik tekshira olmaydi («Tekshirilmadi» deb ko'rsatadi).

Server `wsgi.py` dagi `app` obyektini `gunicorn` orqali ishga tushiradi (Flask'ning o'z serveri faqat
ishlab chiqish uchun — ishlab chiqarishda `gunicorn` ishlatiladi):

```bash
pip install -e .[deploy]      # gunicorn o'rnatadi
DEOBF_PUBLIC=1 gunicorn --bind 0.0.0.0:8000 --threads 4 --timeout 180 wsgi:app
```
