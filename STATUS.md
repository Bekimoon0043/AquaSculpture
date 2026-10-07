# LuxuryForm Studio — Development Status Scorecard

Scored against `LUXURYFORM_SCOPE.md` §Scorecard (0 = nonexistent … 5 = production-grade).
Updated: initial build (Phases 0–2 + first figurative archetype).

**Overall weighted score: ≈ 70%** (target: 80%+ AND all safety-critical gates ≥ 4/5)

| # | System | Weight | Score | Where we stand / next step |
|---|--------|--------|-------|----------------------------|
| 1 | AI Concept Generation | 4% | **3** | Interpreter chain + deterministic multi-concept generator (/api/concepts: 3-4 engineered variants with cost+gate verdicts). Next: LLM narrative per concept, image input |
| 2 | Parametric Geometry | 7% | **4** | 9 archetypes, validated vs analytic volume/bbox, integrity-gated, full param→recalc loop proven via copilot/optimize |
| 3 | Geometry Integrity | 5% | **4** | G2 validated: open/non-manifold/degenerate/floating/min-feature + fold-angle (dihedral) formability limits, tested vs broken meshes. Next: BVH self-intersection |
| 4 | Material Engineering | 4% | **2** | 10 materials with full property set (yield/tensile/E/thermal/corrosion/weldability/finishes). Next: AI material recommendation by environment+loads |
| 5 | Structural Load Engine | 7% | **3** | Dead + wind (gust, drag, solidity per family) + water jet reaction + seismic base shear. Next: snow/maintenance/thermal loads, site wind input |
| 6 | Structural/FEA Analysis | 7% | **3** | In-house 3D frame FEA (direct stiffness, 12-DOF beam elements, validated vs cantilever theory within 2%), auto-section-upsize design loop, FEA safety factors in G4. Next: shell FEA, CalculiX bridge |
| 7 | Foundation/Anchors | 4% | **3** | Base plate + bolt tension SF + pad with soil bearing check + rebar. Next: pull-out calcs + foundation drawing output |
| 8 | Hydraulic Engineering | 7% | **4** | Full network: branch pipes + fitting K-losses, manifold, valve sizing, jet trajectory/height, filtration sizing, pump/nozzle/valve/pipe schedules. Next: pressure-dependent balancing, surge transients |
| 9 | Water Simulation | 4% | **3** | Ballistic jets + Gerstner surface + mist/foam + engineered splash zones (radius from jet height) drawn in viewer. Next: wind drift, splash containment map |
| 10 | Pump/Equipment Selection | 3% | **3** | Pump/nozzle/valve/pipe/filter schedules auto-generated + priced in BOM. Next: real pump curves + supplier model selection |
| 11 | Lighting Engineering | 5% | **3** | Placement engine (uplight ring + submersible), full fixture specs, PSU/DMX/cable/voltage-drop engineering, fixture schedule, G6 gate live. Next: wider fixture catalog, zoning |
| 12 | Lighting Simulation | 3% | **3** | Per-face lux with heat-map overlay in the 3D viewer (Lux toggle). Next: glare analysis, reflected-light bounce |
| 13 | Dynamic Lighting | 3% | **3** | Timeline engine + editor UI (add/edit segments, effects, zones, colors) feeding the brief. Next: music sync via AquaFlow |
| 14 | Kinetic Engineering | 3% | **2** | Rotation/oscillation: mesh-derived inertia, torque, motor+gearbox selection, shaft sizing, bearing L10 life, motion envelope. In BOM. Next: collision envelopes vs surroundings, dynamic stress via FEA |
| 15 | Structural Skeleton Generator | 5% | **3** | Spine + shell-reaching ribs + base frame; SHS auto-selected from base moment (Z_req); viewer x-ray mode; BOM uses real member weight. Next: diagrid/bracing, multiple spine layouts |
| 16 | Panelization | 4% | **3** | Shell auto-panelized (sector×band), flat patterns via PCA+hull, curvature classification, stock-sheet check, G7 gate live. Next: developable-surface unrolling for double-curved panels |
| 17 | Welding Engineering | 3% | **3** | Weld type/size/passes from plate thickness, electrode kg, sequence + distortion + post-weld finish spec, consumables in BOM. Next: per-joint WPS |
| 18 | Internal Service Routing | 3% | **2** | Water risers + power/DMX follow spine with enforced separation, bend-radius check, IP68 penetration schedule, drainage + hatch layout. Next: route geometry in 3D viewer |
| 19 | Maintainability | 2% | **3** | 8-class serviceability analysis (pump/nozzle/lighting/valve/drain/internal/cleaning/corrosion), G8 gate live, deep-basin nozzle flag works. Next: time/stock-based service schedules |
| 20 | Fabrication Sequencing | 2% | **3** | 12-step method statement + crew-days auto-recalibrated from actual project data (learning loop). Next: resource leveling, Gantt export |
| 21 | BOM | 3% | **3** | Itemized XLSX BOM auto-generated from geometry. Next: category expansion (control/mechanical), BOQ format |
| 22 | Cost/Quotation | 3% | **3** | Full cost tree, contingency/margin, budget check, opex. Next: quotation document, regional price books |
| 23 | Engineering AI Copilot | 4% | **3** | Consequence engine + Copilot UI tab (scale slider -> live diff table + notes). Next: LLM wrapper (needs credits), multi-param edits |
| 24 | Multi-Agent Review | 2% | **2** | /api/review: 6 domain reviewers (design/structural/hydraulic/lighting/fabrication/cost) + Chief Engineer with safety-first precedence. Rule-based; LLM wraps when keys funded |
| 25 | Optimization | 2% | **4** | Single-goal search + Pareto front (cost vs weight), gates as hard constraints, validated in tests. Next: continuous solver |
| 26 | CAD/Manufacturing Export | 4% | **4** | STL + GLB + DXF cutting sheets + STEP AP214 faceted BREP in ZIP. Next: GA drawings, IGES, STEP import QA in CAD kernel |
| 27 | Engineering Documentation | 3% | **3** | PDF report + quotation page + XLSX BOM + GA drawing DXF (plan/front/side silhouettes + dims) + method statement in ZIP. Next: dedicated discipline reports, weld drawings |
| 28 | Visualization | 2% | **3** | Viewport + studio lighting + water animation + skeleton x-ray + finish-accurate materials. Next: night mode, site photos |
| 29 | AquaFlow Integration | 2% | **3** | LUXEXCHANGE v1 export live: nozzles+flows, lights+DMX patch, pump/valves, embedded glTF, /api/integration/aquaflow. Next: AquaFlow-side import test, show-program return path |
| 30 | Learning/CogniNet | 2% | **3** | Store + actuals delta analysis + automatic crew-day recalibration feeding new estimates. Next: CogniNet bridge, supplier price learning |

## Design gates (scope §28) — current state

| Gate | Status |
|------|--------|
| G0 Brief Complete | ✅ schema-validated briefs |
| G1 Concept Approved | ⚠️ single concept, manual approval |
| G2 Geometry Valid | ✅ live mesh forensics gate |
| G3 Material Valid | ✅ live (materials DB check) |
| G4 Structural PASS | ✅ live (safety-factor verdict) |
| G5 Hydraulic PASS | ✅ live (flow consistency) |
| G9 Cost PASS | ✅ live (budget check) |
| G1, G6–G8, G10 | ⏳ report as not_evaluated until subsystems exist |

## Near-term priorities (highest weight × lowest score)

1. **Structural/FEA (6)** and **Structural Loads (5)** — safety-critical, 14% combined
2. **Geometry Integrity gate (3)** — safety-critical, cheap to start (manifold + connectivity checks)
3. **Hydraulic network depth (8→4)** — safety-critical, already functional
4. **Skeleton generator (15)** — unlocks panelization (16), welding (17), routing (18)
5. **Material properties DB (4)** — feeds everything above
