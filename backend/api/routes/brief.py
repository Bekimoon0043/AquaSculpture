import json
from pathlib import Path

import jsonschema
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/brief", tags=["brief"])

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "design-brief.schema.json"

EXAMPLE_BRIEF = {
    "project": {"name": "Atrium Crescent", "site": "hotel atrium", "budget_usd": 250000},
    "sculpture": {
        "family": "stacked_c_rings",
        "height_m": 4.0,
        "material": "stainless_316l",
        "finish": "mirror_polish_8",
        "parameters": {"ring_count": 3, "opening_deg": 90, "taper": 0.15},
        "style_notes": "rising, aspirational",
    },
    "water": {
        "features": [
            {"type": "curtain_between_elements"},
            {"type": "bubbler_field", "count": 12},
        ],
        "basin": {
            "shape": "circular",
            "diameter_m": 6,
            "depth_m": 0.45,
            "material": "black_granite",
            "overflow": "perimeter_weir",
        },
    },
    "lighting": {"sculpture_uplights": 4, "submersible_rgb": 12},
    "constraints": {"wind_zone": "moderate", "indoor": False, "public_access": True},
}


def _load_schema() -> dict:
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


class ValidateResponse(BaseModel):
    valid: bool
    errors: list[str] = []


@router.post("/validate", response_model=ValidateResponse)
def validate_brief(brief: dict):
    schema = _load_schema()
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(brief), key=lambda e: list(e.absolute_path))
    messages = [
        f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}" for e in errors
    ]
    return ValidateResponse(valid=not messages, errors=messages)


@router.get("/example")
def get_example_brief():
    return EXAMPLE_BRIEF
