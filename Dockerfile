# Internetga chiqarish uchun konteyner. Standart holatda (DEOBF_PUBLIC=1) tashrif buyuruvchining kodi serverda
# ISHGA TUSHIRILMAYDI (docs/04_internetga_chiqarish.md), shuning uchun gcc kerak emas.
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir "anthropic>=1.0,<2" "pydantic>=2.0,<3" "flask>=3.0,<4" "gunicorn==23.0.0"

COPY deobf_agent ./deobf_agent
COPY samples ./samples
COPY wsgi.py ./
RUN pip install --no-cache-dir --no-deps -e .

# root bo'lmagan foydalanuvchi: konteyner buzilsa ham zarar cheklangan bo'ladi
RUN useradd -m -u 10001 deobf && chown -R deobf /app
USER deobf

# public rejim: serverda kalit saqlanmaydi, kod ishga tushirilmaydi, cheklovlar qattiq.
# Render bitta proksi orqasida ishlaydi (DEOBF_TRUSTED_PROXIES=1): haqiqiy mijoz IP'si tezlik cheklovi uchun olinadi.
ENV DEOBF_PUBLIC=1 DEOBF_TRUSTED_PROXIES=1 PORT=8000
EXPOSE 8000
# Bitta jarayon, ko'p oqim: natijalar va cheklovlar jarayon xotirasida saqlanadi (bir nechta jarayon bo'lsa, yuklab
# olish havolasi tasodifiy 404 beradi). exec — SIGTERM gunicorn'ga yetib borsin.
CMD exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 8 --worker-class gthread --timeout 120 --access-logfile - wsgi:app
