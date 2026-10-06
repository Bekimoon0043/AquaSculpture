# SculptFlow Studio — Master Plan

**Prompt-to-engineering design software for sculptures and fountains.**
The user types what they want. The software designs it, engineers it, prices it, and delivers the 3D model + full documentation package.

- Status: Planning (v1.1 — updated with reference portfolio analysis)
- Platform: Windows desktop app (Electron)
- AI: Hybrid (AI interprets the prompt → deterministic engine does all geometry/engineering/cost)
- Project folder: `E:\ollama` (all work happens here)
- Relationship to AquaFlow Studio: **READ-ONLY REFERENCE ONLY. Never add, edit, or delete any file in the AquaFlow folder** (`E:\Burook platform development\Luxurycon\aquaflow-phase1-stabilization-clean`). No runtime dependency on it.

---

## 1. Vision & User Flow

```
User prompt (natural language)
  e.g. "A 4 m mirror-polished stainless infinity-loop sculpture with water
        sheeting down its inner face, on a 6 m circular black granite basin
        with 12 bubble jets, for a hotel atrium, budget $250k"
        │
        ▼
[1] AI Interpreter (cloud LLM) ──► Structured Design Brief (validated JSON)
        │
        ▼
[2] Geometry Engine (deterministic) ──► 3D sculpture mesh + basin + hydraulics layout
        │
        ▼
[3] Engineering Engine (deterministic) ──► all calculations
        │    geometry / structural / fabrication / hydraulics / electrical / water treatment
        ▼
[4] Cost Engine (deterministic) ──► itemized BOM + capex/opex estimate
        │
        ▼
[5] Deliverables ──► interactive 3D preview + export package:
        GLB/OBJ/STL · DXF drawings · PDF engineering report · XLSX BOM & cost
```

**Core principle:** the AI is only allowed to produce *creative intent as structured data*. Every number that matters (dimensions, volumes, pipe sizes, pump duty, steel tonnes, cost) is computed by deterministic, testable engineering code — never guessed by the AI.

---

## 2. Reference Portfolio — the bar we must meet and exceed

These are real works already built (by another process). SculptFlow's archetype library is defined so that **each of these can be reproduced from a one-line prompt — and the generator families then extend beyond them.** This portfolio is the acceptance test for the geometry engine.

### 2.1 Portfolio analysis

| # | Work | Form family | Material / finish | Water integration | Context |
|---|------|-------------|-------------------|-------------------|---------|
| P1 | Illuminated arc array + Africa-map centerpiece | **Arc-fin radial array** (curved tapered fins on radial layout) + **perforated relief panel** (silhouette map with LED dot matrix) | Brushed stainless fins, LED backlit perforated panel | Rain curtains between arcs, RGB foam-jet field | Circular granite fountain basin, plaza |
| P2 | Twisted white ring ("seed") | **Twisted torus / möbius loop** | GRC / fiberglass, matte white paint | Bubble-jet field around base | Rectangular black granite reflecting pool, residential plaza |
| P3 | Bronze flame-wing | **Ribbed organic flame** (stacked flowing lobes) | Cast bronze / brass finish, patinated | Still basin | Circular marble basin, interior atrium |
| P4 | Tall ribbon knot | **Open ribbon knot/loop** (vertical figure-eight freeform) | Bronze, dark patina | Still basin | Circular marble basin, atrium with oculus |
| P5 | Flowing mirror form (indoor) | **Freeform fluid/flame** with integral spillways | Mirror-polished stainless (#8) | **Water sheets off the sculpture body**, mushroom bubblers | Rectangular stainless basin, hotel lobby |
| P6 | Crescent ring with inner figure | **Open crescent ring + suspended inner silhouette** (bird/boat form) | Mirror-polished stainless | None (dry) | Factory photo — H1.9 × L2.0 × W0.4 m, base plate mount |
| P7 | Tall infinity flame | **Vertical double-loop / figure-eight flame** | Mirror-polished stainless | None (dry) | Garden lawn, ~5–6 m |
| P8 | Stacked loops & saucers | **Stacked open rings + elliptical disks** (vertical totem composition) | Mirror-polished stainless | None (dry) | Garden courtyard |
| P9 | Stacked C-rings fountain | **Stacked open C-rings** (increasing diameter, textured faces) | Brushed + textured stainless | **Water curtain between rings**, perimeter mist | Circular black granite basin, outdoor park |

### 2.2 Design DNA extracted (what the generator must parametrize)

- **Form families present:** loops/rings (open, closed, twisted), ribbons (knotted, flamed, flowing), stacked compositions (rings, disks, totems), radial arc arrays, silhouette/relief panels, crescents with suspended inners.
- **Materials in use:** mirror-polished stainless 304/316L (#8), brushed/hairline stainless, textured/hammered stainless, cast bronze (polished or patinated), brass, GRC/fiberglass with automotive paint, perforated illuminated metal, black granite/marble basins.
- **Water integration patterns:** (a) still reflecting basin, (b) bubbler/foam-jet field, (c) water sheet/curtain falling *from* the sculpture, (d) rain curtain *between* elements, (e) perimeter weir overflow — often combined.
- **Scale range:** 1.9 m courtyard pieces → 6+ m landmark pieces.
- **Fabrication reality:** these are **sheet-metal-over-armature** (stainless, GRC) or **section-cast** (bronze) constructions — hollow shells, internal steel skeletons, welded seams, segmented for transport, bolted to foundations/base plates. The engineering engine must design them this way, not as solid blocks.
- **Lighting:** integrated LED (backlit perforation, uplights on fins, submersible RGB in basins).

### 2.3 "More than these" — how the system exceeds the portfolio

1. Every portfolio piece becomes a **parametric family** — infinite variations (size, count, twist, spacing, material, water pattern), not one fixed shape.
2. **Composition engine**: mixes families (e.g. crescent + ribbon knot + water curtain) under coherence rules.
3. **AI-driven novelty**: the LLM proposes parameter combinations and narratives within validated ranges — variations no one has sketched yet, all instantly engineered and priced.
4. **Instant engineering + cost**: what previously took weeks of drafting and estimation comes out in one session.

---

## 3. The Structured Design Brief (the contract)

The AI interpreter outputs a single JSON document — the contract between AI and engineering. Everything downstream consumes only this.

```jsonc
{
  "project":   { "name": "...", "site": "hotel atrium", "budget_usd": 250000 },
  "sculpture": {
    "family": "stacked_c_rings",        // see §5 archetype library
    "height_m": 4.0,
    "material": "stainless_316l",
    "finish": "mirror_polish_8",         // mirror | brushed | textured | patina | painted
    "parameters": { "ring_count": 3, "opening_deg": 90, "taper": 0.15 },
    "style_notes": "rising, aspirational"
  },
  "water": {
    "features": [
      { "type": "curtain_between_elements" },
      { "type": "bubbler_field", "count": 12 }
    ],
    "basin": { "shape": "circular", "diameter_m": 6, "depth_m": 0.45,
               "material": "black_granite", "overflow": "perimeter_weir" }
  },
  "lighting": { "sculpture_uplights": 4, "submersible_rgb": 12 },
  "constraints": { "wind_zone": "moderate", "indoor": false, "public_access": true }
}
```

A JSON Schema (`schemas/design-brief.schema.json`) validates every AI response; invalid output is retried or falls back to clarification questions shown to the user. The user can always edit the brief manually before engineering runs.

---

## 4. Architecture

```
sculptflow-studio/
├── PLAN.md                     ← this document
├── schemas/                    ← design-brief JSON schema, engineering IR schema
├── backend/                    ← Python 3.11 + FastAPI (local, port 8100)
│   ├── main.py
│   ├── ai/
│   │   ├── interpreter.py      ← prompt → design brief (Anthropic/OpenAI API)
│   │   ├── clarifier.py        ← asks user when prompt is ambiguous
│   │   └── prompts/            ← system prompts + few-shot examples (incl. portfolio)
│   ├── geometry/
│   │   ├── archetypes/         ← parametric sculpture generators (§5)
│   │   ├── mesh_ops.py         ← boolean, loft, sweep, shell/thicken, decimate, slice
│   │   ├── basin.py            ← parametric basin/pool geometry + weirs
│   │   └── layout.py           ← siting, clearances, nozzle/light placement
│   ├── engineering/
│   │   ├── geo_calc.py         ← surface area, volume, CoG, wind projected area
│   │   ├── structural.py       ← armature skeleton, wind load (ASCE 7 / EN 1991),
│   │   │                         foundation, anchor bolts, overturning
│   │   ├── fabrication.py      ← sheet panelization & unroll, weld seam layout,
│   │   │                         casting segmentation, transport modules, molds
│   │   ├── hydraulics.py       ← weir/curtain flow, network solver, pipe sizing, pump duty
│   │   ├── water_treatment.py  ← turnover, filtration, dosing
│   │   └── electrical.py       ← loads, cable sizing, LED drivers, IP-rated schedule
│   ├── cost/
│   │   ├── materials_db.py     ← material price catalog (JSON, editable)
│   │   ├── fabrication.py      ← labor-hour models per material/process/finish
│   │   ├── equipment.py        ← pumps, nozzles, lights, filters catalog
│   │   └── estimator.py        ← capex + opex rollup, contingency, margin
│   ├── deliverables/
│   │   ├── export_3d.py        ← GLB / OBJ / STL (maquette + fabrication)
│   │   ├── drawings.py         ← DXF plans/sections/elevations + panel cutting sheets
│   │   ├── report.py           ← PDF engineering + cost report
│   │   └── bom.py              ← XLSX BOM & cost breakdown
│   └── data/                   ← catalogs: materials, finishes, nozzles, pumps,
│                                 lighting, fabrication rates (JSON)
├── frontend/                   ← React 18 + Vite + Three.js
│   └── src/
│       ├── components/
│       │   ├── PromptConsole.jsx    ← prompt input + clarification chat
│       │   ├── Viewer3D.jsx         ← preview: orbit, section, measure, water anim
│       │   ├── BriefEditor.jsx      ← edit the design brief manually
│       │   ├── EngineeringPanel.jsx ← all calculated values, live
│       │   ├── CostPanel.jsx        ← itemized cost tree
│       │   └── ExportPanel.jsx      ← deliverables download
│       └── store/                   ← Zustand; design brief = single source of truth
├── desktop/                    ← Electron 33 shell + electron-builder NSIS installer
└── tests/                      ← pytest (backend) + vitest (frontend)
```

**Stack decisions**
- Backend: Python + FastAPI — best ecosystem for engineering math (numpy, scipy, trimesh, shapely).
- 3D mesh work: `trimesh` + `shapely` + `manifold3d` (booleans) + `numpy-stl`.
- Frontend: React + Three.js; backend is the geometry authority, the viewer only renders.
- Desktop: Electron + PyInstaller-bundled backend (packaging recipe proven by AquaFlow — read its `desktop/` only as reference).
- Persistence: project files on disk as JSON + exported artifacts (no database).

---

## 5. The Geometry Engine — archetype library

The archetype library is **derived directly from the reference portfolio (§2)** — every family below reproduces at least one built work, then extends it parametrically. Each generator takes the brief's `parameters` and emits a watertight mesh + engineering metadata (shell thickness, armature attachment points, spill edges, segment split lines).

### 5.1 Portfolio families (must-have, Phase 3 at latest)

| Generator | Reproduces | Key parameters |
|---|---|---|
| `twisted_torus` | P2 | major/minor radius, twist count, section morph (round→lens), tilt |
| `open_ring` | P6, P7 bases | diameter, section profile, opening angle, plane tilt |
| `crescent_inner` | P6 | crescent arc, inner silhouette (2D profile extruded/lofted), suspension gap |
| `ribbon_knot` | P4, P7 | centerline curve (knot/wave/flame presets), ribbon width/thickness taper, twist |
| `organic_flame` | P3, P5 | lobe count, flow-curve stack, ribbing, surface noise, integral spill lips |
| `stacked_rings` | P8, P9 | element list (rings/disks/saucers), diameters, openings, offsets, textures |
| `arc_fin_array` | P1 | fin count, arc radius, taper profile, radial layout, LED channel grooves |
| `relief_panel` | P1 centerpiece | silhouette from vector outline (map/logo/custom), perforation density, LED dot grid |

### 5.2 Beyond-portfolio families (the "more than these")

- `torus_knot` (p,q mathematical knots), `mobius_ribbon`, `wave_surface`, `geodesic_shell`, `voronoi_shell` (cast/fabricated with thickness), `spiral_column`, `heightfield_relief` (terrain/portrait reliefs on walls).
- **Composition engine**: vertical stacking rules, nesting (ring-in-ring), radial repetition, plinth mounting — lets the AI compose families into new wholes.

### 5.3 Shared machinery

- Loft/sweep core: profile curves along arbitrary centerlines (covers rings, ribbons, flames).
- Shell & thicken: every sculpture is a hollow shell (sheet or casting thickness) with internal armature interface — never solid.
- Water detailing: weir lips, spill edges, curtain slots generated on the sculpture surface per the brief's water features.
- Basin: circular/rect/ellipse/polygon, perimeter weirs, black-granite cladding presets, nozzle/light auto-placement with clearance rules.
- Maquette workflow: any design exports at 1:10 (or any scale) as STL for 3D-printed client-approval models.

---

## 6. The Engineering Engine

All deterministic, all unit-tested, all shown with formulas and standards references.

**Geometry quantities** (`geo_calc.py`)
- Surface area (finish/polish/patina m²), shell volume → mass via material density
- Center of gravity, bounding box, footprint, wind projected area per orientation
- Section slicing for drawings

**Structural** (`structural.py`)
- Internal armature design: steel skeleton sized for self-weight + wind (these tall thin loop/ribbon forms are wind-critical — see P6/P7)
- Wind load per ASCE 7-22 / EN 1991-1-4, overturning moment, base shear
- Foundation/base plate: pad sizing, anchor bolt schedule, concrete m³, rebar (~110 kg/m³)
- Segment joint checks for transport-split sculptures
- (Phase 4: optional real FEA via CalculiX; v1 uses code-based hand calcs)

**Fabrication engineering** (`fabrication.py`) — *what turns a pretty mesh into a buildable work*
- Sheet-metal path (stainless/GRC): panelization of the shell into workable panels, flat-pattern unrolls for cutting, weld seam map, polish-access check
- Casting path (bronze): segmentation into castable sections, wall thickness check, weld/pin assembly plan, mold count
- Transport & install: largest module dims/weights, crane lift points, assembly sequence
- Finish spec: polish grade area, patina type, paint system

**Hydraulics** (`hydraulics.py`)
- Sculpture-borne water: weir/sheeting flow (Francis weir), curtain slot flow, drip-edge detailing
- Basin features: bubbler/foam jets (Q = K√P), rain curtains
- Network: pipe sizing by velocity bands, Hazen-Williams losses, TDH, pump duty + motor kW
- Basin volume, turnover, surge/displacement from sculpture immersion
- (AquaFlow's `hydraulic_solver.py` is the methodological reference only — we write our own.)

**Water treatment** (`water_treatment.py`) — turnover time → filtration sizing, skimmers, dosing schedule.

**Electrical** (`electrical.py`) — pump/LED/lighting loads, LED driver schedule (incl. perforated-panel dot grids), cable sizing, breaker schedule, IP68 submersible equipment.

---

## 7. The Cost Engine

Itemized tree, every line traceable to a calculation. Fabrication-heavy, matching how these works are actually built:

```
SCULPTURE SHELL   shell mass × $/kg (316L sheet / bronze cast / GRC)
                  + panelization labor hrs × rate  +  finish (mirror polish hrs/m²)
ARMATURE          steel t × $/t + cutting/welding hrs
FOUNDATION        excavation m³, concrete m³, rebar t, anchors, base plate
BASIN             structure, waterproofing m², granite/marble cladding m², weir trims
MECHANICAL        pumps, nozzles, curtain slots, pipes, valves, filtration, treatment
ELECTRICAL        LED (uplights, submersible RGB, panel dot grids), drivers, cabling, panels
FABRICATION OVERHEAD  molds (GRC/casting), jigs, QA, shop drawings
TRANSPORT & INSTALL   modules, cranage, site labor, assembly, commissioning
─────────────────────────────────────────────────────────────
SUBTOTAL → contingency % → design fee % → margin % → TOTAL  (vs. brief budget)
+ annual operating cost (energy, water, chemicals, maintenance)
```

All prices in editable JSON catalogs (`backend/data/`) with currency/region fields. The same tree renders in the UI, the PDF report, and the XLSX BOM.

---

## 8. Deliverables (what the user gets from one prompt)

1. **Interactive 3D model** (orbit, section cuts, measurements, water animation, finish-accurate materials: mirror/brushed/patina)
2. **3D exports**: GLB, OBJ, STL (full size + maquette scale)
3. **Drawings (DXF)**: plan, sections, elevations with dimensions + **panel cutting sheets / flat patterns** for fabrication
4. **PDF engineering report**: brief, quantities, structural (wind/armature/foundation), fabrication plan, hydraulics, electrical — with standards references
5. **XLSX BOM + cost breakdown**
6. **One ZIP** with everything + SHA-256 manifest

---

## 9. Roadmap

**Phase 0 — Skeleton (wk 1–2)**
Electron shell + FastAPI boot, health checks, empty 3D viewer, design-brief schema, project save/load.

**Phase 1 — Core deterministic loop, no AI (wk 3–6)**
Manual brief editor → 2 generators (`open_ring`, `twisted_torus`) + circular/rect basin → geo quantities + hydraulics v1 → cost v1 → GLB/STL + PDF/XLSX. End-to-end proof.

**Phase 2 — AI interpreter (wk 7–8)**
Prompt → brief via cloud LLM, schema validation, clarification loop. Few-shot library **seeded with the 9 portfolio works** ("describe P5" → its brief) so the AI learns the house style.

**Phase 3 — Portfolio archetype pack + engineering depth (wk 9–14)**
All §5.1 generators, sculpture-borne water (sheets/curtains), structural (wind/armature/foundation), fabrication module (panelization/casting split), DXF drawings, LED lighting, ZIP package. **Acceptance: all 9 portfolio works reproducible from prompts, each with full engineering + cost.**

**Phase 4 — Beyond (wk 15+)**
§5.2 beyond-portfolio families + composition engine, water animation polish, maquette pipeline, real-time re-costing while tweaking, CalculiX FEA, project templates, render-quality materials.

---

## 10. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Freeform figurative work (horses, faces) beyond portfolio style | Portfolio style is abstract/loop/ribbon — play to that strength first; figurative is a later archetype (skeleton+loft) |
| AI emits invalid/absurd briefs | JSON schema + validation + retry + clarification; user edits brief before engineering |
| Tall thin loops are genuinely wind-critical | Structural module mandatory for any dry/tall piece; red-flag report when margins are thin |
| Engineering liability | Calcs cite standards; report carries "preliminary — requires licensed engineer review" disclaimer |
| Cost data goes stale | Editable JSON price catalogs, currency/region fields |

---

## 11. Non-goals for v1

- No hardware/PLC control, no show choreography, no music sync (that's AquaFlow)
- No web/multi-user collaboration
- No photorealistic rendering (clean finish-accurate technical visualization is enough)

---

## 12. AquaFlow reference policy

- **Never modify, add, or delete any file** in `E:\Burook platform development\Luxurycon\aquaflow-phase1-stabilization-clean`.
- Read-only methodological references: hydraulic solver approach (`backend/services/hydraulic_solver.py`), brief→concept pipeline (`generative_designer.py`), XLSX/PDF/DXF writer patterns (`bom_generator.py`, `engineering_package.py`), export architecture (`frontend/src/export3d/`), Electron packaging (`desktop/`).
- No code copying; SculptFlow is a fresh codebase.
