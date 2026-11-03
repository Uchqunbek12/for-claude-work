# 04. Internetga chiqarish (deploy)

Bu yo'riqnoma vositani internetga — hamma kira oladigan manzilga — qanday qo'yishni tushuntiradi.
Maqsad: siz havolani (masalan `https://deobf-agent.onrender.com`) ulashasiz, boshqalar brauzerda ochib
sinab ko'radi.

> **Ikki asosiy qoida.**
> 1. Internetdagi serverga **o'z API kalitingizni QO'YMANG.** Aks holda har bir begona odam sizning hisobingiz
>    hisobidan Claude'ga so'rov yuboradi. Shuning uchun vositada **public rejim** bor: server kalit saqlamaydi.
> 2. Begona odamning kodini **serveringizda ishga tushirmang.** Vosita "to'liq tekshiruv" uchun kodni gcc bilan
>    kompilyatsiya qilib ishga tushiradi. O'z kompyuteringizda bu xavfsiz (kodni o'zingiz berasiz), internetda esa
>    xavfli. Public rejimda bu **standart holatda o'chirilgan** (pastda 2-bo'lim).

---

## 1. Ikki rejim farqi

| | Shaxsiy rejim (kompyuteringizda) | Public rejim (internetda) |
|---|---|---|
| Kim ishlatadi | faqat siz | hamma |
| API kalit | `.env` dagi sizning kalitingiz | **server kalit saqlamaydi**; Claude kerak bo'lsa, tashrif buyuruvchi O'Z kalitini kiritadi (u hech qayerda yozilmaydi) |
| Standart dvigatel | Sonnet 5.5 (Claude) | **Offline** (bepul, Claude'siz) |
| Tashrif buyuruvchi kodi | gcc bilan kompilyatsiya qilinadi va sinab ko'riladi → «Tasdiqlandi» | **ishga tushirilmaydi** → natija «Tekshirilmadi» |
| Cheklovlar | yumshoq | kirish ≤ 20 000 belgi, ≤ 3 funksiya, 90 s umumiy vaqt, bir vaqtda 2 tahlil, 10 daqiqada 15 tahlil va 6 kalit tekshiruvi (har bir mijoz IP'si uchun), disk kesh o'chirilgan |
| Himoya sarlavhalari | bor | bor (qat'iy CSP: skriptlar faqat o'zimizdan, `X-Frame-Options`, `Referrer-Policy`, HTTPS'da HSTS) |
| Boshqa saytdan so'rov | rad etiladi (`Host`/`Origin`/`Sec-Fetch-Site` tekshiruvi) | rad etiladi (`Origin`) |

Public rejim `DEOBF_PUBLIC=1` muhit o'zgaruvchisi (yoki `deobf web --public`) bilan yoqiladi. Hamma cheklov
`deobf_agent/web/app.py` va `deobf_agent/sandbox.py` ichida.

**Nega «Tekshirilmadi»?** Tekshiruv (differensial test) kodni haqiqatan ishga tushiradi. Cheklovlar (vaqt, xotira) bu
yerda **haqiqiy izolyatsiya emas**: ishga tushgan dastur serverning boshqa jarayonlari, fayllari va xotirasiga tegishi
mumkin (jumladan boshqa tashrif buyuruvchining o'sha paytdagi kalitiga). Mustaqil audit buni aniq ko'rsatdi,
shuning uchun public rejim standart holatda bu qadamni bajarmaydi. Offline natijadagi har bir soddalashtirish baribir
tasodifiy qiymatlar bilan **hisoblab** tekshiriladi (kodni ishga tushirmasdan, Python ichida) — lekin butun funksiya
bo'yicha tekshiruv emas. To'liq tekshiruv uchun vositani o'z kompyuteringizda ishlating.

---

## 2. Xavfsizlik qatlamlari

1. **Kalit saqlanmaydi.** Serverda hech qanday maxfiy kalit yo'q. Public rejimda `.env` va muhit kaliti
   **ishlatilmaydi** (`wsgi.py`, `llm.py`); tashrif buyuruvchi kalitini kiritmasa, Claude ishlamaydi.
   Kalit faqat shu so'rov uchun ishlatiladi, sahifaga qaytarilmaydi, jurnalga yozilmaydi.
2. **Kod ishga tushirilmaydi** (yuqorida). Operator buni faqat o'zi javob bersa, `DEOBF_NATIVE=1` bilan yoqishi mumkin —
   **faqat** ishonchli izolyatsiya bo'lsa: alohida konteyner/VM (gVisor, Firecracker va h.k.), tarmoqsiz, hech qanday
   maxfiy qiymatsiz, har so'rovda yangilanadigan. Oddiy Docker konteyneri yetarli emas. Bunday izolyatsiyasiz yoqmang.
3. **Cheklovlar:** kirish hajmi, funksiyalar soni, umumiy vaqt, bir vaqtdagi tahlillar (`503`), tezlik (`429`).
   Tezlik cheklovi mijoz IP'si bo'yicha. Render kabi proksi orqasida `DEOBF_TRUSTED_PROXIES=1` o'rnatiladi
   (`render.yaml` da bor), shunda haqiqiy mijoz IP'si olinadi; to'g'ridan-to'g'ri internetga ochilsa, bu o'zgaruvchini
   **o'rnatmang** (aks holda soxta `X-Forwarded-For` bilan cheklovni aylanib o'tish mumkin).
4. **Boshqa saytlardan himoya:** `Origin` mos kelmasa yoki `Sec-Fetch-Site: cross-site` bo'lsa, so'rov rad etiladi
   (CSRF). Shaxsiy rejimda `Host` ham tekshiriladi (DNS rebinding).
5. **Root bo'lmagan foydalanuvchi:** konteynerda server oddiy foydalanuvchi (UID 10001) nomidan ishlaydi.
6. **Qat'iy CSP:** `highlight.js` ham loyihaning o'zidan beriladi (CDN yo'q), shuning uchun `script-src 'self'`.
7. **Aniq versiyalar:** `Dockerfile` da `gunicorn==23.0.0` va kutubxonalarning major versiyalari qotirilgan.

---

## 3. Eng oson yo'l: Render.com (bepul, Docker)

Repozitoriyadagi `Dockerfile` va `render.yaml` tayyor.

1. Kodingizni GitHub'ga joylang (bu repozitoriya allaqachon GitHub'da).
2. [render.com](https://render.com) da ro'yxatdan o'ting, GitHub hisobingizni ulang.
3. **New → Blueprint** tanlang va shu repozitoriyani ko'rsating. Render `render.yaml` ni o'qib,
   `DEOBF_PUBLIC=1` va `DEOBF_TRUSTED_PROXIES=1` bilan Docker servisini yaratadi.
4. **Create** bosing. Birinchi qurilish 2–4 daqiqa davom etadi.
5. Tayyor bo'lgach, Render `https://<nom>.onrender.com` havolasini beradi. Shuni ulashing.

Nozik jihatlar:
- **Bepul reja «uxlab qoladi».** 15 daqiqa foydalanilmasa server to'xtaydi; keyingi ochilish 30–60 soniya
  sekinroq bo'ladi. Demo uchun bu normal.
- **Bitta jarayon.** `Dockerfile` da `--workers 1 --threads 8`: yuklab olish havolalari va cheklovlar jarayon
  xotirasida saqlanadi, shuning uchun bir nechta jarayon bo'lsa havolalar tasodifiy «topilmadi» berardi. Server qayta
  ishga tushsa, eski hisobot havolalari o'chadi.
- **gcc kerak emas:** public rejimda kod ishga tushirilmaydi, shuning uchun konteynerga gcc o'rnatilmaydi.
- **Hali Docker'da sinalmagan:** quriladigan qadamlar (toza muhitga o'rnatish, `gunicorn wsgi:app`) Docker'siz
  qayta ishlab, ishlashi tekshirilgan, lekin haqiqiy `docker build` bu kompyuterda ishga tushirilmagan.

---

## 4. O'zingiz sinab ko'rish

Internetga qo'yishdan oldin public rejimni o'z kompyuteringizda sinab ko'ring:

```bash
deobf web --public
```

Brauzerda `http://127.0.0.1:5000` ochiladi, lekin public rejim ko'rinishida: standart dvigatel — Offline, Claude
uchun kalit maydoni bor, cheklovlar yoqilgan, kod ishga tushirilmaydi. `Ctrl+C` bilan to'xtatiladi.

Docker bilan (Docker o'rnatilgan bo'lsa):

```bash
docker build -t deobf-agent .
docker run -p 8000:8000 deobf-agent
# brauzerda http://127.0.0.1:8000
```

---

## 5. Boshqa xostinglar

`Dockerfile` oddiy, shuning uchun Docker qabul qiladigan har qanday xostingda ishlaydi (Fly.io, Railway, o'z VPS'ingiz).
Ikki narsani ta'minlang:

- `DEOBF_PUBLIC=1` o'rnatilgan bo'lsin;
- proksi orqasida bo'lsangiz — `DEOBF_TRUSTED_PROXIES=<proksilar soni>`.

Server `wsgi.py` dagi `app` obyektini `gunicorn` orqali ishga tushiradi (Flask'ning o'z serveri faqat ishlab chiqish
uchun):

```bash
pip install -e ".[deploy]"      # gunicorn o'rnatadi (qo'shtirnoq zsh uchun kerak)
DEOBF_PUBLIC=1 gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 8 --timeout 120 wsgi:app
```
