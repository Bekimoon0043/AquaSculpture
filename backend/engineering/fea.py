"""Mini 3D frame FEA (scope §6) — Euler-Bernoulli beam-column elements.

Direct stiffness method: 12-DOF beam elements (2 nodes x 6 DOF), global
assembly, fixed base, nodal loads from wind + dead load, numpy solve.
Runs on the generated skeleton members — a genuine structural analysis,
not a hand formula. Validated against cantilever theory in tests.

Output feeds gate G4 alongside the cantilever estimates.
"""

import numpy as np

from fabrication.skeleton import shs_properties

YIELD_PA = 250.0e6  # S275-class design yield used by the G4 check
STEEL_E = 200e9
STEEL_G = 77e9


def _local_stiffness(L, A, E, G, Iy, Iz, J):
    """12x12 local stiffness of a 3D Euler-Bernoulli beam element."""
    k = np.zeros((12, 12))
    a1 = E * A / L
    a2 = G * J / L
    for I, dofs in ((Iz, (2, 6)),):  # bending about z uses Iz (local y disp)
        pass
    b1 = 12 * E * Iz / L**3
    b2 = 6 * E * Iz / L**2
    b3 = 4 * E * Iz / L
    b4 = 2 * E * Iz / L
    c1 = 12 * E * Iy / L**3
    c2 = 6 * E * Iy / L**2
    c3 = 4 * E * Iy / L
    c4 = 2 * E * Iy / L
    # axial (x)
    k[0, 0] = k[6, 6] = a1
    k[0, 6] = k[6, 0] = -a1
    # torsion (about x)
    k[3, 3] = k[9, 9] = a2
    k[3, 9] = k[9, 3] = -a2
    # bending about z (deflection in y): dofs 1,5,7,11
    k[1, 1] = k[7, 7] = b1
    k[1, 7] = k[7, 1] = -b1
    k[1, 5] = k[5, 1] = k[1, 11] = k[11, 1] = b2
    k[5, 7] = k[7, 5] = k[7, 11] = k[11, 7] = -b2
    k[5, 5] = k[11, 11] = b3
    k[5, 11] = k[11, 5] = b4
    # bending about y (deflection in z): dofs 2,4,8,10
    k[2, 2] = k[8, 8] = c1
    k[2, 8] = k[8, 2] = -c1
    k[2, 4] = k[4, 2] = k[4, 8] = k[8, 4] = -c2
    k[2, 10] = k[10, 2] = k[8, 10] = k[10, 8] = -c2
    k[4, 4] = k[10, 10] = c3
    k[4, 10] = k[10, 4] = c4
    return k


def _rotation(p1, p2):
    """3x3 direction-cosine matrix: local x along the element."""
    x = p2 - p1
    L = float(np.linalg.norm(x))
    x = x / L
    up = np.array([0.0, 0.0, 1.0]) if abs(x[2]) < 0.9 else np.array([0.0, 1.0, 0.0])
    y = np.cross(up, x)
    y /= np.linalg.norm(y)
    z = np.cross(x, y)
    return np.stack([x, y, z]), L


def solve_frame(members: list[dict], section: tuple[int, int],
                lateral_load_n: float, dead_load_n: float,
                load_height_m: float) -> dict:
    """Assemble and solve the skeleton frame.

    members: skeleton member dicts with from/to (m). section: SHS (side, wall)
    mm applied to ALL members (ribs are lighter in reality — conservative).
    lateral_load_n applied at the node nearest load_height_m (wind resultant);
    dead_load_n distributed over top-half nodes.
    """
    # Collect unique nodes (all member endpoints).
    nodes: list[np.ndarray] = []
    index: dict[tuple, int] = {}

    def node_id(p):
        key = tuple(np.round(p, 6))
        if key not in index:
            index[key] = len(nodes)
            nodes.append(np.asarray(p, dtype=float))
        return index[key]

    raw = [(node_id(m["from"]), node_id(m["to"])) for m in members]

    # Subdivide members at intermediate nodes lying on them (a rib landing
    # mid-spine must become a real junction, not a floating element).
    elements: list[tuple[int, int]] = []
    for a, b in raw:
        p1, p2 = nodes[a], nodes[b]
        seg = p2 - p1
        L2 = float(seg @ seg)
        if L2 < 1e-12:
            continue
        on = []
        for i, p in enumerate(nodes):
            t = float((p - p1) @ seg / L2)
            if 1e-9 < t < 1 - 1e-9:
                closest = p1 + t * seg
                if float(np.linalg.norm(p - closest)) < 1e-6:
                    on.append((t, i))
        chain = [a] + [i for _, i in sorted(on)] + [b]
        elements.extend(zip(chain, chain[1:]))
    n = len(nodes)
    if n == 0 or not elements:
        raise ValueError("empty frame")

    A = shs_properties(*section)["area_m2"]
    I = shs_properties(*section)["i_m4"]
    J = 2 * I  # thin-wall square tube torsion constant approximation

    K = np.zeros((6 * n, 6 * n))
    for a, b in elements:
        R, L = _rotation(nodes[a], nodes[b])
        if L < 1e-6:
            continue
        k = _local_stiffness(L, A, STEEL_E, STEEL_G, I, I, J)
        T = np.zeros((12, 12))
        for i in range(4):
            T[3 * i:3 * i + 3, 3 * i:3 * i + 3] = R
        kg = T.T @ k @ T
        dofs = list(range(6 * a, 6 * a + 6)) + list(range(6 * b, 6 * b + 6))
        for i in range(12):
            for j in range(12):
                K[dofs[i], dofs[j]] += kg[i, j]

    # Boundary conditions: fix nodes at the lowest level (base).
    y_min = min(p[1] for p in nodes)
    fixed = [i for i, p in enumerate(nodes) if p[1] <= y_min + 0.05]
    fixed_dofs = [6 * i + d for i in fixed for d in range(6)]

    # Loads.
    F = np.zeros(6 * n)
    ys = [p[1] for p in nodes]
    y_top = max(ys)
    load_node = min(range(n), key=lambda i: abs(ys[i] - load_height_m))
    F[6 * load_node] += lateral_load_n          # +x wind resultant
    top_nodes = [i for i in range(n) if ys[i] > y_min + 0.5 * (y_top - y_min)]
    for i in top_nodes:
        F[6 * i + 1] -= dead_load_n / len(top_nodes)  # -y gravity

    free = [d for d in range(6 * n) if d not in fixed_dofs]
    u = np.zeros(6 * n)
    u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])

    reactions = K @ u - F
    disp = u.reshape(n, 6)[:, :3]
    max_disp = float(np.linalg.norm(disp, axis=1).max())

    # Member end forces (local) -> stress per element (+ worst).
    worst = 0.0
    member_results: list[dict] = []
    for a, b in elements:
        R, L = _rotation(nodes[a], nodes[b])
        if L < 1e-6:
            continue
        k = _local_stiffness(L, A, STEEL_E, STEEL_G, I, I, J)
        T = np.zeros((12, 12))
        for i in range(4):
            T[3 * i:3 * i + 3, 3 * i:3 * i + 3] = R
        dofs = list(range(6 * a, 6 * a + 6)) + list(range(6 * b, 6 * b + 6))
        f_local = k @ (T @ u[dofs])
        axial = abs(f_local[0]) / A
        moment = max(abs(f_local[4]), abs(f_local[5]),
                     abs(f_local[10]), abs(f_local[11]))
        z = shs_properties(*section)["z_m3"]
        bending = moment / z
        stress = axial + bending
        worst = max(worst, stress)
        member_results.append({
            "nodes": [int(a), int(b)],
            "from": [round(float(x), 4) for x in np.asarray(nodes[a])],
            "to": [round(float(x), 4) for x in np.asarray(nodes[b])],
            "stress_mpa": round(float(stress) / 1e6, 2),
            # utilization = factored stress / yield (1.5 x sigma / 250 MPa)
            "utilization": round(float(stress) * 1.5 / YIELD_PA, 3),
        })

    node_displacements = [
        {"pos": [round(float(x), 4) for x in np.asarray(nodes[i])],
         "d_mm": [round(float(x) * 1000.0, 3) for x in disp[i]]}
        for i in range(n)
    ]

    return {
        "nodes": int(n),
        "elements": len(elements),
        "fixed_nodes": len(fixed),
        "max_displacement_mm": round(float(max_disp) * 1000.0, 3),
        "max_stress_mpa": round(float(worst) / 1e6, 2),
        "base_reaction_kn": round(float(
            np.linalg.norm([reactions[d] for i in fixed
                            for d in (6 * i, 6 * i + 1, 6 * i + 2)]).sum()), 3),
        "model": "3D Euler-Bernoulli frame, direct stiffness",
        "member_results": member_results,
        "node_displacements": node_displacements,
    }
