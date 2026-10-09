"""AI interpreter: natural-language prompt -> validated design brief.

Hybrid architecture (PLAN.md §1): the LLM only produces creative intent as
structured JSON; every engineering number is computed deterministically
downstream. Anthropic is the primary provider, OpenAI the fallback.

The LLM may only choose from the IMPLEMENTED families below — the schema
enum lists future families too, but those would fail in the geometry engine.
"""

import json
import os
import re
from pathlib import Path

import httpx
import jsonschema

from config import SCHEMA_PATH
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

IMPLEMENTED_FAMILIES = (
    "open_ring", "crescent_inner", "ribbon_knot", "organic_flame",
    "stacked_rings", "stacked_c_rings", "twisted_torus",
    "arc_fin_array", "relief_panel", "buddha_seated",
    "torus_knot", "mobius_ribbon", "wave_surface", "spiral_column",
    "geodesic_shell",
)

SYSTEM_PROMPT = """You are the design interpreter for AquaSculptor, a sculpture + fountain design tool.
Convert the user's request into ONE design brief JSON object. Output ONLY the JSON — no prose, no markdown fences.

Required shape:
{
  "project": {"name": str, "site": str, "budget_usd": number | null},
  "sculpture": {"family": one of IMPLEMENTED_FAMILIES, "height_m": number,
                "material": one of MATERIALS, "finish": one of FINISHES,
                "parameters": object, "style_notes": str},
  "water": {"features": [{"type": one of WATER_FEATURES, "count"?: int,
                          "spill_edge_length_m"?: number, "head_m"?: number}],
            "basin": {"shape": "circular" | "rectangular",
                      "diameter_m"?: number, "length_m"?: number, "width_m"?: number,
                      "depth_m": number, "material": str,
                      "overflow": "perimeter_weir" | "slot_overflow" | "skimmer" | "none"}},
  "lighting": {"sculpture_uplights"?: int, "submersible_rgb"?: int},
  "constraints": {"wind_zone": "low" | "moderate" | "high" | "extreme", "indoor": bool, "public_access": bool}
}

IMPLEMENTED_FAMILIES (choose ONLY from these) with typical parameters:
- open_ring: open ring/crescent. params: diameter_m, tube_radius_m, opening_deg (0-180), tilt_deg
- crescent_inner: crescent ring with a suspended inner silhouette. params: diameter_m, tube_radius_m, opening_deg, inner_shape ("bird"|"boat"), suspension_gap_m
- ribbon_knot: vertical ribbon knot/flame. params: height_m, preset ("figure_eight"|"flame"|"wave"), width_m, thickness_m, twist_deg
- organic_flame: stacked flowing lobes, good for bronze flames and mirror-polished fluid forms with water spilling off. params: height_m, lobe_count, base_radius_m, flow_m, rib_amplitude, spill_lips (bool)
- stacked_rings / stacked_c_rings: vertical totem of open C-rings and disks. params: elements (list of {"type": "ring"|"disk", "diameter_m", "opening_deg"?, "thickness_m", "z_gap_m"})
- twisted_torus: twisted closed ring ("seed" sculptures). params: major_radius_m, section_width_m, section_depth_m, twist_count, tilt_deg, morph (0 round .. 1 lens)
- arc_fin_array: radial array of curved tapered fins (landmark entrances). params: fin_count, height_m, arc_radius_m, layout_diameter_m, base_width_m, tip_width_m
- relief_panel: silhouette relief panel (maps, logos) with optional LED perforation grid. params: thickness_m, perforation_dot_spacing_m
- buddha_seated: seated Buddha in meditation pose on lotus pedestal (figurative). params: height_m, pedestal (bool)
- torus_knot: mathematical knot sculpture. params: p, q, major_radius_m, tube_radius_m
- mobius_ribbon: möbius strip with thickness. params: radius_m, width_m, thickness_m
- wave_surface: undulating ribbon wall. params: width_m, height_m, waves, amplitude_m
- spiral_column: helical tube rising. params: height_m, radius_m, turns, tube_radius_m
- geodesic_shell: geodesic sphere/dome. params: diameter_m, subdivisions

MATERIALS: stainless_304, stainless_316l, bronze, brass, grc, fiberglass, corten_steel, aluminum
FINISHES: mirror_polish_8, mirror, brushed, hairline, textured, hammered, polished, patina, painted
WATER_FEATURES: still_basin, bubbler_field (needs count), foam_jet_field (needs count),
  water_sheet, curtain_from_sculpture, curtain_between_elements (use spill_edge_length_m, head_m),
  rain_curtain, perimeter_mist, perimeter_weir

Design rules:
- Basin should comfortably contain the sculpture: circular basin diameter >= 1.5x sculpture footprint.
- Indoor or prompt says lobby/atrium -> constraints.indoor = true, wind_zone "low".
- Tall dry outdoor pieces -> wind_zone "moderate" or "high".
- Mirror-polished stainless = material stainless_316l, finish mirror_polish_8.
- If the user gives a budget, set project.budget_usd; otherwise null.
- If the user gives no water feature, use a still_basin only.
"""


class AIUnavailable(RuntimeError):
    """No provider API keys configured."""


class AIFailure(RuntimeError):
    """Providers responded but no valid brief could be produced."""


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in model output")
    return json.loads(text[start:end + 1])


def _validate(brief: dict) -> None:
    jsonschema.validate(brief, SCHEMA)
    family = brief["sculpture"]["family"]
    if family not in IMPLEMENTED_FAMILIES:
        raise ValueError(f"family '{family}' is not implemented; choose from {IMPLEMENTED_FAMILIES}")


def _call_anthropic(prompt: str, feedback: str | None) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise AIUnavailable("ANTHROPIC_API_KEY not set")
    user = prompt if not feedback else (
        f"{prompt}\n\nYour previous answer was invalid: {feedback}\n"
        "Return a corrected JSON brief only.")
    resp = httpx.post(
        ANTHROPIC_URL,
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
              "max_tokens": 1500, "system": SYSTEM_PROMPT,
              "messages": [{"role": "user", "content": user}]},
        timeout=60.0,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def _call_openai_compatible(url: str, key_env: str, model_env: str,
                            default_model: str, prompt: str,
                            feedback: str | None) -> str:
    key = os.environ.get(key_env)
    if not key:
        raise AIUnavailable(f"{key_env} not set")
    user = prompt if not feedback else (
        f"{prompt}\n\nYour previous answer was invalid: {feedback}\n"
        "Return a corrected JSON brief only.")
    resp = httpx.post(
        url,
        headers={"Authorization": f"Bearer {key}", "content-type": "application/json"},
        json={"model": os.environ.get(model_env, default_model),
              "response_format": {"type": "json_object"},
              "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                           {"role": "user", "content": user}]},
        timeout=60.0,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_deepseek(prompt: str, feedback: str | None) -> str:
    return _call_openai_compatible(DEEPSEEK_URL, "DEEPSEEK_API_KEY",
                                   "DEEPSEEK_MODEL", "deepseek-chat",
                                   prompt, feedback)


def _call_openai(prompt: str, feedback: str | None) -> str:
    return _call_openai_compatible(OPENAI_URL, "OPENAI_API_KEY",
                                   "OPENAI_MODEL", "gpt-4o-mini",
                                   prompt, feedback)


def interpret(prompt: str) -> tuple[dict, str]:
    """Prompt -> (validated design brief, provider name).

    Provider order: DeepSeek, Anthropic, OpenAI. One retry per provider with
    the validation error fed back to the model.
    """
    if not any(os.environ.get(k) for k in
               ("DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY")):
        raise AIUnavailable("no AI provider keys configured")

    errors: list[str] = []
    for provider, call in (("deepseek", _call_deepseek),
                           ("anthropic", _call_anthropic),
                           ("openai", _call_openai)):
        feedback = None
        for _attempt in range(2):  # first try + one correction retry
            try:
                raw = call(prompt, feedback)
                brief = _extract_json(raw)
                _validate(brief)
                return brief, provider
            except AIUnavailable as e:
                errors.append(str(e))
                break  # no key for this provider — move on
            except (httpx.HTTPError, KeyError, IndexError) as e:
                errors.append(f"{provider}: {e}")
                break  # transport/API failure — try next provider
            except (ValueError, jsonschema.ValidationError) as e:
                feedback = str(e)[:500]  # bad JSON/schema — retry with feedback
                errors.append(f"{provider} invalid output: {feedback}")
    raise AIFailure("; ".join(errors) or "all providers failed")
