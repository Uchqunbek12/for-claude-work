# Internetga chiqarish uchun konteyner.
#
# Standart (xavfsiz) holat: DEOBF_PUBLIC=1 — hammaga ochiq sayt: kod ishga tushirilmaydi, kalit serverda yo'q.
# Yopiq sayt (render.yaml shu holatni sozlaydi): DEOBF_ACCESS_CODE (kirish kodi) va ANTHROPIC_API_KEY berilsa, server kaliti va
# to'liq tekshiruv AVTOMATIK yoqiladi: tekshirilayotgan kod (gcc + differensial test) quyidagi huquqsiz "sandbox" foydalanuvchisi
# nomidan ishlaydi; server esa root bo'lib qoladi: sandbox foydalanuvchisi serverning muhit o'zgaruvchilarini (API kalit) va
# xotirasini o'qiy olmaydi. Docker qurish vaqtida hech qanday maxfiy qiymat yo'q.
FROM python:3.12-slim

# gcc — kodni kompilyatsiya qilib sinash uchun (to'liq tekshiruv yoqilganda ishlatiladi)
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir "anthropic>=1.0,<2" "pydantic>=2.0,<3" "flask>=3.0,<4" "gunicorn==23.0.0"

COPY deobf_agent ./deobf_agent
COPY samples ./samples
COPY wsgi.py ./
RUN pip install --no-cache-dir --no-deps -e .

# Huquqsiz foydalanuvchi: tekshirilayotgan kod shu nomdan ishlaydi (uy papkasi yo'q, kirish imkoni yo'q).
# /app fayllari root'ga tegishli, shuning uchun sandbox foydalanuvchisi ularni o'zgartira olmaydi.
RUN useradd --system --uid 10002 --no-create-home --shell /usr/sbin/nologin sandbox

# DEOBF_TRUSTED_PROXIES=1: Render bitta proksi orqasida — haqiqiy mijoz IP'si tezlik cheklovi uchun olinadi.
ENV DEOBF_PUBLIC=1 DEOBF_TRUSTED_PROXIES=1 DEOBF_SANDBOX_UID=10002 PORT=8000
EXPOSE 8000
# Bitta jarayon, ko'p oqim: natijalar va cheklovlar jarayon xotirasida saqlanadi (bir nechta jarayon bo'lsa, yuklab
# olish havolasi tasodifiy 404 beradi). exec — SIGTERM gunicorn'ga yetib borsin.
CMD exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 8 --worker-class gthread --timeout 120 --access-logfile - wsgi:app
