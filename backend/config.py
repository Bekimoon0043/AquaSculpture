"""Configuration: dependency-free .env loader + bundle-aware paths.

PyInstaller onefile puts bundled read-only assets under sys._MEIPASS;
writable data (.env, projects, knowledge store) lives beside the exe.
"""

import os
import sys
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)
if FROZEN:
    RESOURCE_ROOT = Path(sys._MEIPASS)                    # bundled assets
    APP_DIR = Path(sys.executable).resolve().parent       # beside the exe
else:
    RESOURCE_ROOT = Path(__file__).resolve().parents[1]   # repo root
    APP_DIR = Path(__file__).resolve().parent             # backend/

ENV_PATH = APP_DIR / ".env" if FROZEN else RESOURCE_ROOT / ".env"
# Catalogs (read-only): bundled "data/" when frozen, backend/data/ in dev.
DATA_DIR = (RESOURCE_ROOT / "data") if FROZEN else Path(__file__).resolve().parent / "data"
# Writable stores (projects, knowledge): beside the exe when frozen.
WRITE_DIR = (APP_DIR / "data") if FROZEN else Path(__file__).resolve().parent / "data"
SCHEMA_PATH = RESOURCE_ROOT / "schemas" / "design-brief.schema.json"
FRONTEND_DIST = RESOURCE_ROOT / "frontend" / "dist"


def load_env(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


load_env()
