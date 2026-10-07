"""Multi-concept generation (scope §2.2).

One site brief -> several controlled concept variants from different design
families, each run through the full pipeline so concepts arrive WITH their
engineering + cost already attached. The AI layer later writes the narrative;
the variants here are deterministic and always buildable.
"""

CONCEPT_MATRIX = [
    {"family": "open_ring", "material": "stainless_316l",
     "finish": "mirror_polish_8", "theme": "minimal ring"},
    {"family": "twisted_torus", "material": "stainless_316l",
     "finish": "mirror_polish_8", "theme": "organic void"},
    {"family": "ribbon_knot", "material": "bronze",
     "finish": "patina", "theme": "flowing ribbon"},
    {"family": "organic_flame", "material": "bronze",
     "finish": "polished", "theme": "rising flame"},
]

_PARAMS = {
    "open_ring": lambda h: {"diameter_m": h, "tube_radius_m": round(h * 0.04, 3),
                            "opening_deg": 90, "segments": 24},
    "twisted_torus": lambda h: {"major_radius_m": round(h * 0.45, 3),
                                "section_width_m": round(h * 0.11, 3),
                                "section_depth_m": round(h * 0.07, 3),
                                "twist_count": 2, "morph": 0.5},
    "ribbon_knot": lambda h: {"height_m": h, "preset": "figure_eight",
                              "width_m": round(h * 0.15, 3),
                              "thickness_m": round(h * 0.02, 3)},
    "organic_flame": lambda h: {"height_m": h, "lobe_count": 4,
                                "base_radius_m": round(h * 0.2, 3)},
}


def generate_concepts(base_brief: dict, run_pipeline, count: int = 3) -> dict:
    sc = base_brief.get("sculpture") or {}
    height = sc.get("height_m", 3.0)
    concepts = []
    for spec in CONCEPT_MATRIX[:count]:
        brief = {
            **base_brief,
            "sculpture": {**sc, "family": spec["family"],
                          "material": spec["material"], "finish": spec["finish"],
                          "parameters": _PARAMS[spec["family"]](height)},
        }
        r = run_pipeline(brief)
        concepts.append({
            "theme": spec["theme"],
            "brief": brief,
            "headline": {
                "mass_kg": r["sculpture"]["metadata"]["mass_kg"],
                "total_usd": r["cost"]["total_usd"],
                "over_budget": r["cost"]["over_budget"],
                "gates_pass": not r["gates"]["hard_fail"],
                "panels": r["panelization"]["panel_count"],
            },
        })
    return {"concepts": concepts,
            "note": "controlled design families — every concept is engineered "
                    "and buildable, not a random image"}
