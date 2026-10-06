"""Archetype registry: family name -> generator function (PLAN.md §5.1)."""

import inspect

from geometry.archetypes.arc_fin_array import generate_arc_fin_array
from geometry.archetypes.buddha_seated import generate_buddha_seated
from geometry.archetypes.crescent_inner import generate_crescent_inner
from geometry.archetypes.open_ring import generate_open_ring
from geometry.archetypes.organic_flame import generate_organic_flame
from geometry.archetypes.relief_panel import generate_relief_panel
from geometry.archetypes.ribbon_knot import generate_ribbon_knot
from geometry.archetypes.stacked_rings import generate_stacked_rings
from geometry.archetypes.twisted_torus import generate_twisted_torus

GENERATORS = {
    "open_ring": generate_open_ring,
    "twisted_torus": generate_twisted_torus,
    "ribbon_knot": generate_ribbon_knot,
    "organic_flame": generate_organic_flame,
    "stacked_rings": generate_stacked_rings,
    "crescent_inner": generate_crescent_inner,
    "arc_fin_array": generate_arc_fin_array,
    "relief_panel": generate_relief_panel,
    "buddha_seated": generate_buddha_seated,
    "stacked_c_rings": generate_stacked_rings,  # §3 brief name for stacked_rings
}

_SIGNATURES = {name: inspect.signature(fn) for name, fn in GENERATORS.items()}


def accepted_parameters(family: str) -> set[str]:
    return set(_SIGNATURES[family].parameters)


def generate(family: str, params: dict, material: str, height_m: float) -> dict:
    """Dispatch a brief's sculpture section to the right generator.

    Only parameters the generator accepts are forwarded; diameter_m /
    height_m fall back to the brief's height where the signature asks for
    them. Raises KeyError for unknown families, ValueError for bad params.
    """
    if family not in GENERATORS:
        raise KeyError(family)
    accepted = accepted_parameters(family)
    kwargs = {k: v for k, v in params.items() if k in accepted}
    if "diameter_m" in accepted and "diameter_m" not in kwargs and height_m:
        kwargs["diameter_m"] = height_m
    if "height_m" in accepted and "height_m" not in kwargs and height_m:
        kwargs["height_m"] = height_m
    if "material" in accepted:
        kwargs.setdefault("material", material)
    return GENERATORS[family](**kwargs)
