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
