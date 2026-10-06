# LuxuryForm Studio — Development Status Scorecard

Scored against `LUXURYFORM_SCOPE.md` §Scorecard (0 = nonexistent … 5 = production-grade).
Updated: initial build (Phases 0–2 + first figurative archetype).

**Overall weighted score: ≈ 36%** (target: 80%+ AND all safety-critical gates ≥ 4/5)

| # | System | Weight | Score | Where we stand / next step |
|---|--------|--------|-------|----------------------------|
| 1 | AI Concept Generation | 4% | **2** | Interpreter live (DeepSeek→Claude→OpenAI chain, schema-validated briefs). Next: multi-concept alternatives, image/sketch input |
| 2 | Parametric Geometry | 7% | **3** | 9 parametric archetypes incl. figurative; parameter change re-runs all engineering. Next: full edit-param→recalc UI, more families |
| 3 | Geometry Integrity | 5% | **3** | G2 gate live: open/non-manifold edges, degenerate faces, floating components (union-find), min feature size. Next: self-intersection BVH, curvature limits |
| 4 | Material Engineering | 4% | **2** | 10 materials with full property set (yield/tensile/E/thermal/corrosion/weldability/finishes). Next: AI material recommendation by environment+loads |
| 5 | Structural Load Engine | 7% | **3** | Dead + wind (gust, drag, solidity per family) + water jet reaction + seismic base shear. Next: snow/maintenance/thermal loads, site wind input |
| 6 | Structural/FEA Analysis | 7% | **2** | Deflection, stress, Euler buckling, natural frequency + resonance screen, safety factors (anchored/freestanding). Next: CalculiX FEA integration |
| 7 | Foundation/Anchors | 4% | **3** | Base plate + bolt tension SF + pad with soil bearing check + rebar. Next: pull-out calcs + foundation drawing output |
| 8 | Hydraulic Engineering | 7% | **3** | Weir/jet flow, pipe sizing (velocity bands), Hazen-Williams, TDH, pump duty, turnover. Next: full network (manifold/branch/valve losses), nozzle trajectory |
| 9 | Water Simulation | 4% | **1** | Flow/height computed numerically; no visual water yet. Next: jet trajectories + water surface in the 3D viewer |
| 10 | Pump/Equipment Selection | 3% | **2** | Duty point + equipment catalog pricing. Next: real pump curves, model selection from supplier DB |
| 11 | Lighting Engineering | 5% | **1** | Fixture counts + cost lines. Next: fixture specs (lumens/beam/IP/DMX), placement engine |
| 12 | Lighting Simulation | 3% | **0** | — Next: lux heat-map estimation |
| 13 | Dynamic Lighting | 3% | **0** | — Next: timeline editor (delegate show control to AquaFlow per scope §31) |
| 14 | Kinetic Engineering | 3% | **0** | — Later phase per scope |
| 15 | Structural Skeleton Generator | 5% | **1** | Armature estimated as % of shell mass. Next: actual member layout (tubes/RHS/ribs) |
| 16 | Panelization | 4% | **1** | Labor-hours estimate only. Next: surface → panels → flat-pattern DXF |
| 17 | Welding Engineering | 3% | **0** | — Next: weld seam map from panelization |
| 18 | Internal Service Routing | 3% | **0** | — Next: pipe/cable routing through sculpture interior |
| 19 | Maintainability | 2% | **0** | — Next: access checks + inspection flags |
| 20 | Fabrication Sequencing | 2% | **0** | — Next: method-statement generator |
| 21 | BOM | 3% | **3** | Itemized XLSX BOM auto-generated from geometry. Next: category expansion (control/mechanical), BOQ format |
| 22 | Cost/Quotation | 3% | **3** | Full cost tree, contingency/margin, budget check, opex. Next: quotation document, regional price books |
| 23 | Engineering AI Copilot | 4% | **1** | Brief-level interpretation works. Next: consequence evaluation ("20% taller → +42% overturning…") |
| 24 | Multi-Agent Review | 2% | **0** | — Next: reviewer roles after copilot matures |
| 25 | Optimization | 2% | **0** | — Next: goal-driven parameter search |
| 26 | CAD/Manufacturing Export | 4% | **2** | STL + GLB export. Next: DXF drawings/flat patterns, then STEP/IGES |
| 27 | Engineering Documentation | 3% | **2** | PDF report + XLSX BOM + ZIP manifest. Next: dedicated structural/hydraulic/foundation reports, GA drawings |
| 28 | Visualization | 2% | **2** | 3D viewport, studio env lighting, finishes. Next: water/night rendering, site integration |
| 29 | AquaFlow Integration | 2% | **0** | — Next: fixture/nozzle/DMX export envelope (read AquaFlow schemas, no code duplication) |
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
