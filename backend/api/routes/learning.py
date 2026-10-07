from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from learning import store

router = APIRouter(prefix="/learning", tags=["learning"])


@router.get("/history")
def get_history():
    return {"runs": store.history()}


@router.get("/similar")
def get_similar(family: str | None = None, height_m: float | None = None,
                material: str | None = None):
    return {"matches": store.similar_projects(family, height_m, material)}


class ActualsRequest(BaseModel):
    run_id: str
    actuals: dict


@router.post("/actuals")
def post_actuals(req: ActualsRequest):
    try:
        return store.record_actuals(req.run_id, req.actuals)
    except KeyError:
        raise HTTPException(status_code=404, detail="run_id not found")
