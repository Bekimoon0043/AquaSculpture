"""Archetype registry: family name -> generator function (PLAN.md §5.1)."""

import inspect
import sys

from geometry.archetypes.arc_fin_array import generate_arc_fin_array
from geometry.archetypes.beyond import (generate_geodesic_shell,
                                        generate_mobius_ribbon,
                                        generate_spiral_column,
                                        generate_torus_knot,
                                        generate_wave_surface)
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
    "torus_knot": generate_torus_knot,
    "mobius_ribbon": generate_mobius_ribbon,
    "wave_surface": generate_wave_surface,
    "spiral_column": generate_spiral_column,
    "geodesic_shell": generate_geodesic_shell,
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


# ── Parameter metadata for generated UI forms (nTop/Grasshopper lesson:
# the parameter chain is the product, so the form comes from the signature,
# not from hand-written per-family UI). Ranges follow naming rules; a
# generator may declare PARAM_CHOICES = {"name": (...)} for enum params.
_HIDDEN = {"material", "shell_thickness_m", "elements", "outline"}
_UNIT_INTERVAL = {"morph", "taper", "aspect_xy", "rib_amplitude"}
_INT_NAMES = {"segments", "tube_segments", "radial_segments", "fin_segments",
              "subdivisions", "p", "q", "waves", "turns"}


def _range_for(name: str, default, is_int: bool) -> dict:
    if name in _UNIT_INTERVAL:
        return {"min": 0.0, "max": 1.0, "step": 0.01}
    if name.endswith("_deg"):
        return {"min": 0.0, "max": 360.0, "step": 1.0}
    if is_int:
        base = max(int(default or 1), 1)
        if name.endswith("_count") or name in ("p", "q", "waves", "subdivisions"):
            return {"min": 1, "max": max(4 * base, 8), "step": 1}
        return {"min": max(base // 4, 3), "max": 4 * base, "step": 1}
    d = float(default or 1.0)
    if name.endswith("_m"):
        return {"min": 0.01, "max": round(max(5.0 * d, 0.5), 2), "step": 0.01}
    return {"min": 0.0, "max": round(max(4.0 * d, 1.0), 2), "step": 0.05}


def param_meta(family: str) -> list[dict]:
    """[{name, type, default, min, max, step, choices?}] for one family."""
    fn = GENERATORS[family]
    choices = getattr(sys.modules[fn.__module__], "PARAM_CHOICES", {})
    out = []
    for p in _SIGNATURES[family].parameters.values():
        if p.name in _HIDDEN or p.default is inspect.Parameter.empty:
            continue
        d = p.default
        if d is None:          # optional override (width_m/depth_m, plate dia)
            continue
        if isinstance(d, bool):
            out.append({"name": p.name, "type": "bool", "default": d})
        elif isinstance(d, str):
            item = {"name": p.name, "type": "str", "default": d}
            if p.name in choices:
                item["choices"] = list(choices[p.name])
            out.append(item)
        elif isinstance(d, int) and (p.annotation is int or p.name in _INT_NAMES):
            out.append({"name": p.name, "type": "int", "default": d,
                        **_range_for(p.name, d, True)})
        elif isinstance(d, (int, float)):
            out.append({"name": p.name, "type": "float", "default": float(d),
                        **_range_for(p.name, d, False)})
    return out


def families_catalog() -> list[dict]:
    """Every registered family with its UI parameter schema."""
    return [{"family": name, "params": param_meta(name)}
            for name in GENERATORS if name != "stacked_c_rings"]
