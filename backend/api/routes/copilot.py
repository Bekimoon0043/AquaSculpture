from fastapi import APIRouter
from pydantic import BaseModel

from engineering.copilot import scale_consequences
from pipeline import run_pipeline

router = APIRouter(prefix="/copilot", tags=["copilot"])


class ScaleRequest(BaseModel):
    brief: dict
    factor: float = 1.2  # "make it 20% taller"


@router.post("/scale")
def copilot_scale(req: ScaleRequest):
    """Deterministic engineering consequence diff for a size change."""
    if not 0.2 <= req.factor <= 5.0:
        from fastapi import HTTPException
        raise HTTPException(status_code=422,
                            detail="factor must be in [0.2, 5.0]")
    return scale_consequences(req.brief, req.factor, run_pipeline)
