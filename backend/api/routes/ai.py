from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ai.interpreter import AIFailure, AIUnavailable, interpret

router = APIRouter(prefix="/ai", tags=["ai"])


class InterpretRequest(BaseModel):
    prompt: str


@router.post("/interpret")
def interpret_prompt(req: InterpretRequest):
    """Natural-language prompt -> validated design brief (PLAN.md §1, Phase 2)."""
    if not req.prompt.strip():
        raise HTTPException(status_code=422, detail="prompt must not be empty")
    try:
        brief, provider = interpret(req.prompt)
    except AIUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    except AIFailure as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"brief": brief, "provider": provider}
