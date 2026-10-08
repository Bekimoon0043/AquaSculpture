"""3D export: ASCII STL and binary GLB (glTF 2.0), dependency-free."""

import json
import struct

import numpy as np


def build_stl(meshes: list[dict]) -> str:
    """One ASCII STL document with a named solid per mesh.

    meshes: [{"name": str, "vertices": [[x,y,z],...], "faces": [[a,b,c],...]}]
    """
    out = []
    for mesh in meshes:
        name = mesh.get("name", "mesh")
        v = np.asarray(mesh["vertices"], dtype=float)
        faces = np.asarray(mesh["faces"], dtype=int)
        out.append(f"solid {name}\n")
        for a, b, c in faces:
            p0, p1, p2 = v[a], v[b], v[c]
            n = np.cross(p1 - p0, p2 - p0)
            norm = np.linalg.norm(n)
            n = n / norm if norm > 0 else np.zeros(3)
            out.append(f"  facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}\n")
            out.append("    outer loop\n")
            for p in (p0, p1, p2):
                out.append(f"      vertex {p[0]:.6e} {p[1]:.6e} {p[2]:.6e}\n")
            out.append("    endloop\n  endfacet\n")
        out.append(f"endsolid {name}\n")
    return "".join(out)


def write_stl_ascii(path, meshes: list[dict]):
    with open(path, "w", encoding="utf-8") as f:
        f.write(build_stl(meshes))


def build_glb(vertices, faces) -> bytes:
    """Minimal valid glTF 2.0 binary: single mesh, POSITION + uint32 indices."""
    v = np.asarray(vertices, dtype="<f4")
    idx = np.asarray(faces, dtype="<u4").reshape(-1)

    pos_bytes = v.tobytes()
    idx_bytes = idx.tobytes()
    bin_blob = pos_bytes
    if len(bin_blob) % 4:
        bin_blob += b"\x00" * (4 - len(bin_blob) % 4)
    idx_offset = len(bin_blob)
    bin_blob += idx_bytes
    if len(bin_blob) % 4:
        bin_blob += b"\x00" * (4 - len(bin_blob) % 4)

    gltf = {
        "asset": {"version": "2.0", "generator": "AquaSculptor"},
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
        "buffers": [{"byteLength": len(bin_blob)}],
    }
    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    if len(json_bytes) % 4:
        json_bytes += b" " * (4 - len(json_bytes) % 4)

    total = 12 + 8 + len(json_bytes) + 8 + len(bin_blob)
    out = struct.pack("<III", 0x46546C67, 2, total)          # magic "glTF", v2
    out += struct.pack("<II", len(json_bytes), 0x4E4F534A)   # JSON chunk
    out += json_bytes
    out += struct.pack("<II", len(bin_blob), 0x004E4942)     # BIN chunk
    out += bin_blob
    return out


def write_glb(path, vertices, faces):
    with open(path, "wb") as f:
        f.write(build_glb(vertices, faces))
