from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ai.interpreter import (AIFailure, AIUnavailable, describe_brief,
                            diff_briefs, interpret, refine)

router = APIRouter(prefix="/ai", tags=["ai"])


class InterpretRequest(BaseModel):
    prompt: str


class RefineRequest(BaseModel):
    brief: dict
    instruction: str


def _chain(fn, *args):
    try:
        return fn(*args)
    except AIUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    except AIFailure as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/interpret")
def interpret_prompt(req: InterpretRequest):
    """Natural-language prompt -> validated design brief (PLAN.md §1, Phase 2).
    `summary` is the deterministic interpretation echo."""
    if not req.prompt.strip():
        raise HTTPException(status_code=422, detail="prompt must not be empty")
    brief, provider = _chain(interpret, req.prompt)
    return {"brief": brief, "provider": provider, "summary": describe_brief(brief)}


@router.post("/refine")
def refine_brief(req: RefineRequest):
    """Apply a natural-language change to an existing brief; returns the
    updated brief plus the exact field changes (deterministic diff)."""
    if not req.instruction.strip():
        raise HTTPException(status_code=422, detail="instruction must not be empty")
    brief, provider = _chain(refine, req.brief, req.instruction)
    return {"brief": brief, "provider": provider,
            "summary": describe_brief(brief),
            "changes": diff_briefs(req.brief, brief)}


@router.post("/describe")
def describe(brief: dict):
    """Interpretation echo for any brief (no AI needed)."""
    return {"summary": describe_brief(brief)}
