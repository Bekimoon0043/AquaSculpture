import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/project", tags=["project"])

PROJECTS_DIR = Path(__file__).resolve().parents[2] / "data" / "projects"

_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _-]{0,63}$")


def _safe_path(name: str) -> Path:
    if not _NAME_RE.match(name):
        raise HTTPException(status_code=400, detail="Invalid project name")
    return PROJECTS_DIR / f"{name}.json"


class ProjectSaveRequest(BaseModel):
    name: str
    data: dict


@router.post("/save")
def save_project(req: ProjectSaveRequest):
    path = _safe_path(req.name)
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump({"name": req.name, "data": req.data}, f, indent=2)
    return {"saved": True, "name": req.name}


@router.get("/list")
def list_projects():
    if not PROJECTS_DIR.exists():
        return {"projects": []}
    names = sorted(p.stem for p in PROJECTS_DIR.glob("*.json"))
    return {"projects": names}


@router.get("/{name}")
def load_project(name: str):
    path = _safe_path(name)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
