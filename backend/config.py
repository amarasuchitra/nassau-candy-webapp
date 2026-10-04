"""Paths and runtime settings for the web application.

Everything is resolved relative to the project root so the app runs the same
locally and on Streamlit Community Cloud.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
DATA_PATH = os.path.join(BASE_DIR, "data", "Nassau_Candy_Distributor.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
WEB_DIR = os.path.join(BASE_DIR, "web")

MODEL_PATH = os.path.join(OUTPUT_DIR, "best_model.joblib")
# Data bundle the dashboard renders from (served by the API).
BUNDLE_PATH = os.path.join(OUTPUT_DIR, "dashboard_bundle.json")
# Same bundle copied next to the page, so the dashboard also works on a
# static host (Netlify / Vercel / GitHub Pages) with no backend.
STATIC_BUNDLE_PATH = os.path.join(WEB_DIR, "data", "dashboard_bundle.json")
# Script version of the same data: lets web/index.html work even when opened
# straight from disk (browsers block fetch() on file:// pages).
STATIC_BUNDLE_JS_PATH = os.path.join(WEB_DIR, "data", "dashboard_bundle.js")

# Optional: set ADMIN_TOKEN to enable POST /api/admin/rebuild (re-runs the
# whole pipeline). Unset = endpoint disabled.
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "").strip()

# Comma-separated list of origins allowed to call the API from another site.
# Default "*" is fine: the API is read-only apart from the token-protected rebuild.
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o.strip()]

APP_VERSION = "2.0.0"

# The original analysis modules import each other as top-level modules
# (e.g. `from constants import ...`), so make src/ importable.
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
