from fastapi import APIRouter

router = APIRouter(tags=["health"])

VERSION = "0.1.0"


@router.get("/health")
def get_health():
    return {"status": "ok", "version": VERSION}
