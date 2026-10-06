from fastapi import APIRouter

from pipeline import generate_sculpture, geo_quantities

router = APIRouter(prefix="/geometry", tags=["geometry"])


@router.post("/generate")
def generate_geometry(brief: dict):
    """Run the geometry engine on a design brief (any registered family)."""
    result = generate_sculpture(brief)
    return {"mesh": {"vertices": result["vertices"], "faces": result["faces"]},
            "metadata": result["metadata"],
            "geo": geo_quantities(result)}
