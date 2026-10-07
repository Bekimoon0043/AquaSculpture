from fastapi import APIRouter
from pydantic import BaseModel

from engineering.concepts import generate_concepts
from pipeline import run_pipeline

router = APIRouter(prefix="/concepts", tags=["concepts"])


class ConceptRequest(BaseModel):
    brief: dict
    count: int = 3


@router.post("")
def concepts(req: ConceptRequest):
    count = max(1, min(req.count, 4))
    return generate_concepts(req.brief, run_pipeline, count=count)
