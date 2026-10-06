"""AquaFlow integration (scope §31): LuxuryForm -> AquaFlow export.

Emits a LUXEXCHANGE v1 envelope — the LuxuryCon inter-platform interchange
format (see AquaFlow frontend/src/export3d/luxexchange.js, read-only
reference): { platform, version, payload_type, source, exported_at,
payload: { scene, stats, gltf, fixtures } }.

The fixture manifest carries the design-level record AquaFlow needs to
program the show: nozzle coordinates + hydraulics identity, light positions
+ DMX patch, pump/valve equipment, water zones. LuxuryForm owns sculpture
engineering; AquaFlow owns show control — no show logic is duplicated here.
"""

import base64
import json
from datetime import datetime, timezone

import numpy as np

LUXEXCHANGE_VERSION = "1.0"
PLATFORM = "LuxuryForm"


def _gltf_document(vertices, faces) -> dict:
    """Self-contained glTF 2.0 JSON document (base64 data-URI buffer)."""
    v = np.asarray(vertices, dtype="<f4")
    idx = np.asarray(faces, dtype="<u4").reshape(-1)
    pos_bytes = v.tobytes()
    idx_bytes = idx.tobytes()
    blob = pos_bytes
    if len(blob) % 4:
        blob += b"\x00" * (4 - len(blob) % 4)
    idx_offset = len(blob)
    blob += idx_bytes
    if len(blob) % 4:
        blob += b"\x00" * (4 - len(blob) % 4)

    uri = "data:application/octet-stream;base64," + base64.b64encode(blob).decode()
    return {
        "asset": {"version": "2.0", "generator": "LuxuryForm Studio"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1,
                                    "mode": 4}]}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(pos_bytes)},
            {"buffer": 0, "byteOffset": idx_offset, "byteLength": len(idx_bytes)},
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": int(len(v)),
             "type": "VEC3", "min": v.min(axis=0).tolist(),
             "max": v.max(axis=0).tolist()},
            {"bufferView": 1, "componentType": 5125, "count": int(len(idx)),
             "type": "SCALAR"},
        ],
        "buffers": [{"byteLength": len(blob), "uri": uri}],
    }


def _fixture_manifest(result: dict) -> list[dict]:
    fixtures: list[dict] = []
    hyd = result.get("hydraulics") or {}
    basin_meta = (result.get("basin") or {}).get("metadata") or {}
    offset_y = result.get("sculpture_offset_m", 0.0)

    # Nozzles: coordinates from the basin layout + hydraulic identity.
    positions = basin_meta.get("nozzle_positions") or []
    jet_features = [f for f in hyd.get("features", []) if f.get("nozzle")]
    per_nozzle = []
    if jet_features:
        total = sum(f["flow_lps"] for f in jet_features)
        per_nozzle_flow = total / len(positions) if positions else 0.0
        nozzle_type = jet_features[0]["nozzle"]
        branch_dn = (jet_features[0].get("pipe") or {}).get("dn")
        for i, pos in enumerate(positions):
            fixtures.append({
                "id": f"NZ{i + 1:03d}",
                "name": f"Nozzle {i + 1}",
                "kind": "nozzle",
                "type": nozzle_type,
                "position": {"x": round(pos[0], 3), "y": round(pos[1], 3),
                             "z": round(pos[2], 3)},
                "rotation": {"x": 0, "y": 0, "z": 0},
                "scale": {"x": 1, "y": 1, "z": 1},
                "material": None,
                "light": None,
                "engineering": {
                    "flow_lps": round(per_nozzle_flow, 3),
                    "branch_dn": branch_dn,
                    "feature": jet_features[0]["type"],
                    "zone": "basin",
                },
            })

    # Lights: positions + DMX patch from the lighting schedule.
    for row in (result.get("lighting") or {}).get("controls", {}).get("schedule", []):
        fx = next((f for f in result["lighting"]["fixtures"]
                   if f["id"] == row["id"]), None)
        pos = fx["position"] if fx else [0, 0, 0]
        fixtures.append({
            "id": row["id"],
            "name": row["fixture"],
            "kind": "light",
            "type": row["fixture"],
            "position": {"x": pos[0], "y": pos[1], "z": pos[2]},
            "rotation": {"x": 0, "y": 0, "z": 0},
            "scale": {"x": 1, "y": 1, "z": 1},
            "material": None,
            "light": {"power_w": row["power_w"], "aim": fx["aim"] if fx else None},
            "engineering": {
                "dmx_address": row["dmx_address"],
                "dmx_channels": row["dmx_channels"],
                "ip": row["ip"],
                "zone": "sculpture" if row["id"].startswith("U") else "basin",
            },
        })

    # Equipment: pump duty + valves (show-relevant state AquaFlow controls).
    pump = hyd.get("schedules", {}).get("pump")
    if pump:
        fixtures.append({
            "id": "PMP01", "name": "Main pump", "kind": "equipment",
            "type": "pump",
            "position": {"x": 0, "y": 0, "z": 0},
            "rotation": {"x": 0, "y": 0, "z": 0},
            "scale": {"x": 1, "y": 1, "z": 1},
            "material": None, "light": None,
            "engineering": {"duty_flow_lps": pump["duty_flow_lps"],
                            "duty_head_m": pump["duty_head_m"],
                            "motor_kw": pump["motor_kw"], "zone": "plant"},
        })
    for i, v in enumerate(hyd.get("schedules", {}).get("valves", [])):
        fixtures.append({
            "id": f"VLV{i + 1:02d}", "name": f"Valve {v['branch']}",
            "kind": "equipment", "type": f"valve_{v['type']}",
            "position": {"x": 0, "y": 0, "z": 0},
            "rotation": {"x": 0, "y": 0, "z": 0},
            "scale": {"x": 1, "y": 1, "z": 1},
            "material": None, "light": None,
            "engineering": {"dn": v["dn"], "branch": v["branch"],
                            "zone": "plant"},
        })
    return fixtures


def build_luxexchange(result: dict) -> dict:
    """Full LUXEXCHANGE v1 envelope from a pipeline result."""
    brief = result.get("brief") or {}
    mesh = result["sculpture"]["mesh"]
    fixtures = _fixture_manifest(result)
    light_count = sum(1 for f in fixtures if f["kind"] == "light")

    return {
        "platform": PLATFORM,
        "version": LUXEXCHANGE_VERSION,
        "payload_type": "scene3d",
        "source": "LuxuryForm Studio",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "payload": {
            "scene": {
                "name": (brief.get("project") or {}).get("name", "LuxuryForm Scene"),
                "generator": "LuxuryForm Studio",
                "generatedAt": datetime.now(timezone.utc).isoformat(),
                "upAxis": "Y",
                "unit": "meter",
            },
            "stats": {
                "nodeCount": 1 + len(fixtures),
                "fixtureCount": len(fixtures),
                "lightCount": light_count,
                "triangleCount": len(mesh["faces"]),
            },
            "gltf": _gltf_document(mesh["vertices"], mesh["faces"]),
            "fixtures": fixtures,
        },
    }
