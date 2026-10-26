"""Entry point for Vercel. Vercel runs the `app` object below as a serverless function.

The real code lives in backend/app. This file only makes it importable.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app  # noqa: E402,F401
