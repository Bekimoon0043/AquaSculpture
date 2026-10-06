import json

from fastapi import APIRouter
from fastapi.responses import Response

from integration.aquaflow import build_luxexchange
from pipeline import run_pipeline

router = APIRouter(prefix="/integration", tags=["integration"])


@router.post("/aquaflow")
def aquaflow_export(brief: dict):
    """Run the pipeline and return a LUXEXCHANGE v1 envelope for AquaFlow."""
    result = run_pipeline(brief)
    envelope = build_luxexchange(result)
    name = (result["brief"].get("project") or {}).get("name", "luxuryform")
    safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in name)
    return Response(
        content=json.dumps(envelope).encode("utf-8"),
        media_type="application/json",
        headers={"Content-Disposition":
                 f'attachment; filename="{safe}.luxexchange.json"'},
    )
