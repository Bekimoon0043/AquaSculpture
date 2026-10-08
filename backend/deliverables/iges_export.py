"""IGES wireframe export (scope §29) — dependency-free.

Entity 110 (Line) per unique mesh edge. IGES is 80-column card format:
S (start), G (global), D (directory, 2 cards per entity), P (parameters),
T (terminate). Wireframe-level IGES imports everywhere; solid IGES (144/143
trimmed surfaces) is a later step — STEP already covers the solid path.
"""


def _pad(text: str, section: str, seq: int) -> str:
    return f"{text:<72}{section}{seq:>7}\n"


def build_iges(vertices, faces, name: str = "sculpture") -> str:
    # Unique undirected edges.
    edge_set = set()
    for a, b, c in faces:
        for e in ((a, b), (b, c), (c, a)):
            edge_set.add((min(e), max(e)))
    edges = sorted(edge_set)

    out: list[str] = []
    out.append(_pad("LuxuryForm Studio IGES wireframe export", "S", 1))

    g_params = ("1H,,1H;,9Hsculpture,7Hout.igs,9HLuxuryForm,9HLuxuryForm,"
                "32,38,6,308,15,;")
    g_len = len(g_params)
    g_card = g_params + " " * max(0, 64 - g_len)
    out.append(_pad(g_card, "G", 1))

    d_cards: list[str] = []
    p_cards: list[str] = []
    p_seq = 0
    for i, (a, b) in enumerate(edges):
        de_line = 2 * i + 1           # directory entry starts on odd cards
        x1, y1, z1 = vertices[a]
        x2, y2, z2 = vertices[b]
        p_seq += 1
        p_data = (f"110,{x1:.4f},{y1:.4f},{z1:.4f},"
                  f"{x2:.4f},{y2:.4f},{z2:.4f},{de_line};")
        p_cards.append(f"{p_data:<64}{de_line:>8}{'P':>1}{p_seq:>7}\n")
        d_cards.append(
            _pad(f"{110:>8}{p_seq:>8}{0:>8}{0:>8}{0:>8}{0:>8}{0:>8}"
                 f"{0:>8}{'00000000':>8}", "D", de_line))
        d_cards.append(
            _pad(f"{110:>8}{0:>8}{0:>8}{1:>8}{0:>8}{0:>8}{'':>8}"
                 f"{'EDGE':>8}{i + 1:>8}", "D", de_line + 1))

    out.extend(d_cards)
    out.extend(p_cards)
    t = (f"S{1:>7}G{1:>7}D{len(d_cards):>7}P{len(p_cards):>7}")
    out.append(_pad(t, "T", 1))
    return "".join(out)


def iges_bytes(vertices, faces, name: str = "sculpture") -> bytes:
    return build_iges(vertices, faces, name).encode("ascii", errors="replace")
