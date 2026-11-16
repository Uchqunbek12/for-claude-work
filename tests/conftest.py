import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import os

import pytest


@pytest.fixture(autouse=True)
def _restore_environ():
    """Testlar (masalan, load_dotenv) os.environ ni o'zgartirsa, keyingi testlarga o'tib ketmasin."""
    saved = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(saved)


@pytest.fixture(autouse=True)
def _no_real_keys(monkeypatch):
    """Dasturchining haqiqiy kalitlari (muhitda yoki .env da) testlar natijasiga ta'sir qilmasin."""
    for name in ("ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY", "DEOBF_MODEL"):
        monkeypatch.delenv(name, raising=False)
