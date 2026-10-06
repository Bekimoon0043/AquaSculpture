# LuxuryForm Studio — Development Status Scorecard

Scored against `LUXURYFORM_SCOPE.md` §Scorecard (0 = nonexistent … 5 = production-grade).
Updated: initial build (Phases 0–2 + first figurative archetype).

**Overall weighted score: ≈ 30%** (target: 80%+ AND all safety-critical gates ≥ 4/5)

| # | System | Weight | Score | Where we stand / next step |
|---|--------|--------|-------|----------------------------|
| 1 | AI Concept Generation | 4% | **2** | Interpreter live (DeepSeek→Claude→OpenAI chain, schema-validated briefs). Next: multi-concept alternatives, image/sketch input |
| 2 | Parametric Geometry | 7% | **3** | 9 parametric archetypes incl. figurative; parameter change re-runs all engineering. Next: full edit-param→recalc UI, more families |
| 3 | Geometry Integrity | 5% | **1** | Watertightness proven in tests for revolve archetypes only. Next: pipeline validation gate (manifold/intersection/connectivity checks) |
| 4 | Material Engineering | 4% | **1** | Catalog has density/cost/shell thickness only. Next: strength/fatigue/weldability properties + AI material recommendation |
| 5 | Structural Load Engine | 7% | **2** | Dead + simplified ASCE 7 wind load. Next: gust factors, mesh vs solid aero, water/dynamic/seismic loads |
| 6 | Structural/FEA Analysis | 7% | **1** | Overturning/shear hand calcs only. Next: buckling/deflection/natural frequency; CalculiX FEA integration |
| 7 | Foundation/Anchors | 4% | **2** | Base plate sizing + 4-bolt tension check + pad volume. Next: pull-out/bearing calcs + foundation drawing output |
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
| G2 Geometry Valid | ⚠️ partial (per-archetype tests, no pipeline gate) |
| G3–G10 | ❌ not implemented as gates yet |

## Near-term priorities (highest weight × lowest score)

1. **Structural/FEA (6)** and **Structural Loads (5)** — safety-critical, 14% combined
2. **Geometry Integrity gate (3)** — safety-critical, cheap to start (manifold + connectivity checks)
3. **Hydraulic network depth (8→4)** — safety-critical, already functional
4. **Skeleton generator (15)** — unlocks panelization (16), welding (17), routing (18)
5. **Material properties DB (4)** — feeds everything above
