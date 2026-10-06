from fastapi import APIRouter

from pipeline import run_pipeline

router = APIRouter(prefix="/engineering", tags=["engineering"])


@router.post("/run")
def run_engineering(brief: dict):
    """Full deterministic loop: brief -> geometry + basin + hydraulics + cost."""
    return run_pipeline(brief)
