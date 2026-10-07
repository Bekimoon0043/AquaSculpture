"""Learning / knowledge system (scope §32) — local foundation.

Every engineering run is logged to an append-only store with its key
predicted metrics. When actual fabrication data arrives (cost, hours,
performance), it attaches to the run and produces predicted-vs-actual
deltas — the feedback loop that makes future estimates smarter.

CogniNet connection later; this file-based store is the contract.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

STORE = Path(__file__).resolve().parents[1] / "data" / "knowledge" / "runs.jsonl"


def _append(record: dict) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    with STORE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _read_all() -> list[dict]:
    if not STORE.exists():
        return []
    return [json.loads(line) for line in
            STORE.read_text(encoding="utf-8").splitlines() if line.strip()]


def log_run(result: dict) -> str:
    """Log a pipeline run; returns the run id."""
    brief = result["brief"]
    sc = brief["sculpture"]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    _append({
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": (brief.get("project") or {}).get("name"),
        "family": sc.get("family"),
        "material": sc.get("material"),
        "finish": sc.get("finish"),
        "height_m": sc.get("height_m"),
        "predicted": {
            "mass_kg": result["sculpture"]["metadata"]["mass_kg"],
            "surface_m2": result["sculpture"]["metadata"]["surface_area_m2"],
            "total_usd": result["cost"]["total_usd"],
            "crew_days": result["method_statement"]["total_crew_days"],
            "pump_kw": result["hydraulics"]["motor_kw"],
            "panel_count": result["panelization"]["panel_count"],
            "weld_m": result["panelization"]["total_weld_seam_m"],
        },
        "gates_pass": not result["gates"]["hard_fail"],
        "actuals": None,
    })
    return run_id


def record_actuals(run_id: str, actuals: dict) -> dict:
    """Attach actuals to a run and compute predicted-vs-actual deltas."""
    rows = _read_all()
    for row in rows:
        if row["run_id"] == run_id:
            row["actuals"] = actuals
            deltas = {}
            for key, actual in actuals.items():
                pred = row["predicted"].get(key)
                if isinstance(pred, (int, float)) and isinstance(
                        actual, (int, float)) and pred:
                    deltas[key] = {
                        "predicted": pred, "actual": actual,
                        "error_pct": round((actual - pred) / pred * 100.0, 1)}
            row["delta_analysis"] = deltas
            STORE.write_text("".join(json.dumps(r) + "\n" for r in rows),
                             encoding="utf-8")
            return {"run_id": run_id, "delta_analysis": deltas}
    raise KeyError(run_id)


def similar_projects(family: str | None = None, height_m: float | None = None,
                     material: str | None = None, tol: float = 0.25) -> list[dict]:
    """Past runs matching family/material and height within ±tol."""
    out = []
    for row in _read_all():
        if family and row["family"] != family:
            continue
        if material and row["material"] != material:
            continue
        if height_m and row.get("height_m"):
            if abs(row["height_m"] - height_m) / height_m > tol:
                continue
        out.append(row)
    return out


def history() -> list[dict]:
    return _read_all()
