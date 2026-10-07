from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from engineering.optimize import optimize
from pipeline import run_pipeline

router = APIRouter(prefix="/optimize", tags=["optimize"])


class OptimizeRequest(BaseModel):
    brief: dict
    goal: str = "cost"


@router.post("")
def optimize_design(req: OptimizeRequest):
    try:
        return optimize(req.brief, req.goal, run_pipeline)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
