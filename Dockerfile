# Internetga chiqarish uchun konteyner. gcc — differensial test (kodni kompilyatsiya qilib
# solishtirish) uchun kerak. Server oddiy (root bo'lmagan) foydalanuvchi nomidan ishlaydi.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt pyproject.toml README.md ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY deobf_agent ./deobf_agent
COPY samples ./samples
RUN pip install --no-cache-dir --no-deps -e .

# root bo'lmagan foydalanuvchi: konteyner buzilsa ham zarar cheklangan bo'ladi
RUN useradd -m -u 10001 deobf && chown -R deobf /app
USER deobf

# public rejim: serverda hech qanday kalit saqlanmaydi, cheklovlar qattiq
ENV DEOBF_PUBLIC=1 PORT=8000
EXPOSE 8000
# threads — differensial test uzoq davom etishi mumkin; timeout keng olingan
CMD gunicorn --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --worker-class gthread --timeout 180 wsgi:app
