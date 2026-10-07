from fastapi import APIRouter

from learning import store
from pipeline import run_pipeline

router = APIRouter(prefix="/engineering", tags=["engineering"])


@router.post("/run")
def run_engineering(brief: dict):
    """Full deterministic loop: brief -> geometry + basin + hydraulics + cost.

    Every run is logged to the knowledge store (scope §32).
    """
    result = run_pipeline(brief)
    try:
        result["run_id"] = store.log_run(result)
    except Exception:
        pass  # learning must never break engineering
    return result
