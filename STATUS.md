# LuxuryForm Studio — Development Status Scorecard

Scored against `LUXURYFORM_SCOPE.md` §Scorecard (0 = nonexistent … 5 = production-grade).
Updated: initial build (Phases 0–2 + first figurative archetype).

**Overall weighted score: ≈ 52%** (target: 80%+ AND all safety-critical gates ≥ 4/5)

| # | System | Weight | Score | Where we stand / next step |
|---|--------|--------|-------|----------------------------|
| 1 | AI Concept Generation | 4% | **2** | Interpreter live (DeepSeek→Claude→OpenAI chain, schema-validated briefs). Next: multi-concept alternatives, image/sketch input |
| 2 | Parametric Geometry | 7% | **3** | 9 parametric archetypes incl. figurative; parameter change re-runs all engineering. Next: full edit-param→recalc UI, more families |
| 3 | Geometry Integrity | 5% | **3** | G2 gate live: open/non-manifold edges, degenerate faces, floating components (union-find), min feature size. Next: self-intersection BVH, curvature limits |
| 4 | Material Engineering | 4% | **2** | 10 materials with full property set (yield/tensile/E/thermal/corrosion/weldability/finishes). Next: AI material recommendation by environment+loads |
| 5 | Structural Load Engine | 7% | **3** | Dead + wind (gust, drag, solidity per family) + water jet reaction + seismic base shear. Next: snow/maintenance/thermal loads, site wind input |
| 6 | Structural/FEA Analysis | 7% | **2** | Deflection, stress, Euler buckling, natural frequency + resonance screen, safety factors (anchored/freestanding). Next: CalculiX FEA integration |
| 7 | Foundation/Anchors | 4% | **3** | Base plate + bolt tension SF + pad with soil bearing check + rebar. Next: pull-out calcs + foundation drawing output |
| 8 | Hydraulic Engineering | 7% | **4** | Full network: branch pipes + fitting K-losses, manifold, valve sizing, jet trajectory/height, filtration sizing, pump/nozzle/valve/pipe schedules. Next: pressure-dependent balancing, surge transients |
| 9 | Water Simulation | 4% | **2** | Live viewer water: ballistic jet particles from real exit velocities, water surface, curtain sheets, gravity animation. Next: splash zones, mist, wind drift |
| 10 | Pump/Equipment Selection | 3% | **3** | Pump/nozzle/valve/pipe/filter schedules auto-generated + priced in BOM. Next: real pump curves + supplier model selection |
| 11 | Lighting Engineering | 5% | **3** | Placement engine (uplight ring + submersible), full fixture specs, PSU/DMX/cable/voltage-drop engineering, fixture schedule, G6 gate live. Next: wider fixture catalog, zoning |
| 12 | Lighting Simulation | 3% | **2** | Point-source lux over shell faces: avg/max/coverage + wasted-fixture detection. Next: heat-map visualization, glare/reflection |
| 13 | Dynamic Lighting | 3% | **0** | — Next: timeline editor (delegate show control to AquaFlow per scope §31) |
| 14 | Kinetic Engineering | 3% | **0** | — Later phase per scope |
| 15 | Structural Skeleton Generator | 5% | **3** | Spine + shell-reaching ribs + base frame; SHS auto-selected from base moment (Z_req); viewer x-ray mode; BOM uses real member weight. Next: diagrid/bracing, multiple spine layouts |
| 16 | Panelization | 4% | **3** | Shell auto-panelized (sector×band), flat patterns via PCA+hull, curvature classification, stock-sheet check, G7 gate live. Next: developable-surface unrolling for double-curved panels |
| 17 | Welding Engineering | 3% | **2** | Weld seam map + total length from panelization, costed in BOM. Next: weld types/sizes, sequence, distortion |
| 18 | Internal Service Routing | 3% | **2** | Water risers + power/DMX follow spine with enforced separation, bend-radius check, IP68 penetration schedule, drainage + hatch layout. Next: route geometry in 3D viewer |
| 19 | Maintainability | 2% | **3** | 8-class serviceability analysis (pump/nozzle/lighting/valve/drain/internal/cleaning/corrosion), G8 gate live, deep-basin nozzle flag works. Next: time/stock-based service schedules |
| 20 | Fabrication Sequencing | 2% | **0** | — Next: method-statement generator |
| 21 | BOM | 3% | **3** | Itemized XLSX BOM auto-generated from geometry. Next: category expansion (control/mechanical), BOQ format |
| 22 | Cost/Quotation | 3% | **3** | Full cost tree, contingency/margin, budget check, opex. Next: quotation document, regional price books |
| 23 | Engineering AI Copilot | 4% | **1** | Brief-level interpretation works. Next: consequence evaluation ("20% taller → +42% overturning…") |
| 24 | Multi-Agent Review | 2% | **0** | — Next: reviewer roles after copilot matures |
| 25 | Optimization | 2% | **0** | — Next: goal-driven parameter search |
| 26 | CAD/Manufacturing Export | 4% | **3** | STL + GLB + flat-pattern DXF cutting sheets in ZIP package. Next: GA drawings, STEP/IGES |
| 27 | Engineering Documentation | 3% | **2** | PDF report + XLSX BOM + ZIP manifest. Next: dedicated structural/hydraulic/foundation reports, GA drawings |
| 28 | Visualization | 2% | **3** | Viewport + studio lighting + water animation + skeleton x-ray + finish-accurate materials. Next: night mode, site photos |
| 29 | AquaFlow Integration | 2% | **3** | LUXEXCHANGE v1 export live: nozzles+flows, lights+DMX patch, pump/valves, embedded glTF, /api/integration/aquaflow. Next: AquaFlow-side import test, show-program return path |
| 30 | Learning/CogniNet | 2% | **0** | — Final phase per scope §32 |

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
