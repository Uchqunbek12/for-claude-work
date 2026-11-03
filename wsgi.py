"""Ishlab chiqarish serveri (gunicorn / Render) uchun kirish nuqtasi.

    gunicorn wsgi:app

Internetga chiqarishda DEOBF_PUBLIC=1 muhit o'zgaruvchisi o'rnatiladi (render.yaml, Dockerfile),
shunda server public rejimda ishlaydi: kalit saqlanmaydi, kirish hajmi va so'rov tezligi cheklanadi,
disk kesh o'chiriladi, xavfsizlik sarlavhalari qo'shiladi (deobf_agent/web/app.py).
"""

from deobf_agent import sandbox
from deobf_agent.llm import load_dotenv
from deobf_agent.web.app import create_app

if not sandbox.PUBLIC:
    load_dotenv()      # mahalliy sinovda .env o'qiladi; public rejimda kalit fayldan hech qachon o'qilmaydi
app = create_app()
