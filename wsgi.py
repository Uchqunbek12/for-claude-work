"""Ishlab chiqarish serveri (gunicorn / Render) uchun kirish nuqtasi.

    gunicorn wsgi:app

Internetga chiqarishda DEOBF_PUBLIC=1 muhit o'zgaruvchisi o'rnatiladi (render.yaml, Dockerfile),
shunda server public rejimda ishlaydi: kalit saqlanmaydi, kirish hajmi va so'rov tezligi cheklanadi,
disk kesh o'chiriladi, xavfsizlik sarlavhalari qo'shiladi (deobf_agent/web/app.py).
"""

from deobf_agent.llm import load_dotenv
from deobf_agent.web.app import create_app

load_dotenv()          # mahalliy sinovda .env bo'lsa o'qiydi (internetda odatda bo'lmaydi)
app = create_app()
