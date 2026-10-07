from fastapi import APIRouter

from engineering.review import review_design
from pipeline import run_pipeline

router = APIRouter(prefix="/review", tags=["review"])


@router.post("")
def review(brief: dict):
    """Six domain reviewers + chief engineer verdict (scope §26)."""
    return review_design(brief, run_pipeline)
