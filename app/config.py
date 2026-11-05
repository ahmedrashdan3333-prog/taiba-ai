"""Central configuration. Everything is overridable through environment variables."""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("TAIBA_DATA_DIR", BASE_DIR / "data"))
SEED_DIR = DATA_DIR / "seed"
KB_DIR = DATA_DIR / "kb"
KB_DOCS_DIR = KB_DIR / "docs"
KB_UPLOADS_DIR = KB_DIR / "uploads"
CURRICULUM_PATH = DATA_DIR / "curriculum.json"
GRADING_PATH = DATA_DIR / "grading.json"
STATIC_DIR = BASE_DIR / "static"

# ---- Institute scoping: this assistant serves ONE institute (Saqqara / Giza). -------------
INSTITUTE_ID = "saqqara"
INSTITUTE_NAME_AR = "معهد طيبة العالى لتكنولوجيا الإدارة والمعلومات - الجيزة (طريق سقارة السياحى)"
INSTITUTE_NAME_EN = "Thebes Higher Institute of Management & Information Technology - Giza (Saqqara Tourist Road)"
OFFICIAL_SITE = "https://thebes.edu.eg/ar"
INSTITUTE_PAGE = ("https://thebes.edu.eg/ar/institutes/"
                  "thebes-higher-institute-of-management-information-technology%20-%20Giza")
# Documents tagged with any other institute (e.g. "maadi") are never loaded or retrievable.
ALLOWED_INSTITUTES = frozenset({INSTITUTE_ID, "academy"})
ALLOWED_FETCH_HOSTS = ("thebes.edu.eg", "tiba.edu.eg")

# ---- Limits -------------------------------------------------------------------------------
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_QUESTION_CHARS = 1000
ALLOWED_UPLOAD_EXT = frozenset({".pdf", ".docx", ".txt", ".md", ".html", ".htm", ".csv"})

# ---- LLM / admin / API --------------------------------------------------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
MODEL = os.getenv("TAIBA_MODEL", "claude-sonnet-5-5")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "").strip()
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "30"))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

# ---- Retrieval ----------------------------------------------------------------------------
TOP_K = 5
MIN_SCORE = 1.2

# ---- Official contact details (from the institute page) -----------------------------------
CONTACT = {
    "phone": "02238093110",
    "email": "thebes.academy@tiba.edu.eg",
    "whatsapp": "https://wa.me/201001771142",
    "facebook": "https://www.facebook.com/GizaThebes/",
    "telegram": "https://t.me/GizaThebes",
    "portal": "http://Portal.tiba.edu.eg",
}
