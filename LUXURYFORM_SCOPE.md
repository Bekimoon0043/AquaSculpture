# LuxuryForm Studio — Complete Development Scope

**This document is the FINAL PRODUCT GOAL and governing scope of the software.**
Saved verbatim from the product owner. `PLAN.md` is the working implementation
plan; where they differ, this scope wins.

Product name: **LuxuryForm Studio** (formerly working title "SculptFlow Studio").

---

## 1. Core objective

LuxuryForm should convert:

Idea / sketch / image / client brief
→ Concept alternatives
→ Parametric 3D sculpture
→ Engineering validation
→ Water-feature engineering
→ Structural engineering
→ Material engineering
→ Lighting engineering
→ Motion/mechatronics engineering
→ Fabrication engineering
→ BOM + costing
→ Production drawings
→ CNC/fabrication files
→ Installation engineering
→ AquaFlow integration
→ Client visualization/rendering

The critical principle is:

**The geometry cannot be separated from the engineering.**

If the AI creates a beautiful 8 m sculpture that cannot withstand wind, cannot be fabricated, has impossible weld access, has inadequate pipe routing, or requires a 40 kW pump to achieve the proposed water effect, the design is a failure.

## 2. STUDIO / CONCEPT DESIGN ENGINE

### 2.1 Design input

LuxuryForm should accept: text descriptions, reference photographs, sketches, logos, existing sculptures, CAD files, 3D models, site photographs, site plans, architectural drawings, client branding, cultural references, material requirements, maximum dimensions, budget, manufacturing constraints.

### 2.2 AI Concept Generator

Generate multiple sculpture concepts according to constraints such as:

- Geometry: height, width, depth, footprint, clearance, center of gravity, symmetry/asymmetry, solid/mesh/perforated construction
- Design language: Organic, Geometric, Figurative, Abstract, Cultural, Architectural, Minimalist, Parametric, Ribbon, Mesh, Faceted

The system should generate controlled design families, not random images.

## 3. PARAMETRIC 3D GEOMETRY ENGINE

One of the most important parts. Every sculpture should become an editable engineering object.

Parameters should include: overall H/W/D, member thickness, plate thickness, tube diameter, curvature, mesh density, perforation, surface subdivision, structural ribs, support spacing, base geometry, anchor locations.

Changing height from 6 m → 8 m should trigger recalculation of structural, hydraulic, material and fabrication properties.

### Geometry integrity

LuxuryForm should automatically detect: self intersections, open meshes, non-manifold geometry, floating components, impossible wall thickness, excessively tight curvature, unconnected members, inaccessible internal areas, fabrication conflicts.

**Hard validation gate:** the production sculpture must resolve into one genuinely connected fabrication body, not merely visually overlapping components.

## 4. MATERIAL ENGINEERING ENGINE

Material database covering at minimum:

- Metals: SS304, SS316, SS316L, SS2205 duplex, mild steel, weathering steel, aluminum, bronze, brass
- Later: FRP, GFRC, concrete, stone, acrylic, polycarbonate, composites

Every material should contain engineering properties: density, yield strength, tensile strength, elastic modulus, thermal expansion, corrosion resistance, fatigue characteristics, weldability, formability, available thicknesses, surface finishing compatibility, cost.

The AI should recommend materials according to: environment + loads + water exposure + fabrication process + appearance + expected lifespan + cost.

## 5. STRUCTURAL ENGINEERING ENGINE

A major subsystem, not a basic stability calculator.

### Loads

- **Dead load** — sculpture self-weight
- **Wind load** — site wind speed, sculpture height, projected surface, drag coefficient, shape factor, gust effects. Mesh sculptures need different aerodynamic treatment from solid sculptures.
- **Water loads** — internal water weight, jet reaction forces, pipe loads, transient forces, vibration, water accumulation
- **Dynamic loads** (moving sculptures) — acceleration, deceleration, rotational forces, motor torque, inertia, cyclic loading, fatigue
- **Other loads** where applicable — seismic, snow, maintenance personnel, accidental loads, thermal expansion

## 6. STRUCTURAL ANALYSIS

Calculate: stress, strain, deflection, buckling, torsion, bending, shear, fatigue, vibration, natural frequency, resonance risk, overturning, sliding.

Produce safety factors for: main structure, secondary structure, connections, anchors, foundation.

The software should eventually integrate an FEA solver rather than relying exclusively on simplified formulas.

## 7. FOUNDATION & ANCHOR ENGINEERING

The sculpture doesn't end at the bottom of the artwork. Calculate: Sculpture → Base plate → Anchors → Foundation → Ground.

Functions: base plate sizing, anchor bolt quantity, anchor diameter, bolt circle, pull-out forces, shear forces, concrete bearing, overturning moment, foundation dimensions, pedestal design.

Output: Installation/Foundation Drawing with dimensions and loads.

## 8. WATER SCULPTURE / HYDRAULIC ENGINE

Should become extremely sophisticated — connects directly to LuxuryCon's fountain expertise and AquaFlow.

Water outlet designer: outlets positioned directly on sculpture geometry. Types: laminar jets, straight jets, sheet waterfalls, cascade, spillways, mist, foam, fan jets, internal water channels, edge overflow, water curtains.

## 9. HYDRAULIC CALCULATION ENGINE

For every water outlet calculate flow Q = A × V, required discharge, velocity, pressure, head, jet height, trajectory, nozzle loss, pipe friction, fitting losses.

Solve the complete hydraulic network: Reservoir → Pump → Filter → Main pipe → Manifold → Branch → Valve → Sculpture → Nozzle.

Outputs: total flowrate, TDH, required pressure, pump duty point, pipe diameter, manifold size, valve sizing, nozzle selection.

## 10. WATER EFFECT SIMULATION

Visual simulation approximating: jet trajectory, water height, waterfall width, sheet thickness, splash zone, mist, gravity, wind influence. The designer modifies pressure / nozzle / orientation / flow and immediately sees the effect.

## 11. PUMP & EQUIPMENT SELECTION

Calculate Q, TDH, motor power, efficiency, operating point; select from LuxuryCon's equipment/supplier database. Generate: pump schedule, nozzle schedule, valve schedule, pipe schedule, filtration requirements, control requirements.

## 12. LIGHTING DESIGN ENGINE

Lighting = engineering + artistic choreography. Each fixture needs: position, direction, beam angle, lumen output, intensity, RGB/RGBW, CCT, CRI, IP rating, power, voltage, control protocol.

## 13. ILLUMINATION SIMULATION

Estimate: illuminance (lux), beam spread, falloff, shadow, reflections (stainless-steel and water), glare, hotspots. Heat-map style illumination analysis — an engineering answer to "where should the lights actually be installed?"

## 14. DYNAMIC LIGHT DESIGN

Timeline editor, e.g. 00:00–00:05 Warm White → 00:05–00:10 Blue Fade → 00:10–00:15 RGB Chase → 00:15–00:20 Water-synchronized pulse. Functions: fade, pulse, chase, gradient, wave, sparkle, strobe, color transition, zone sequencing, music synchronization.

## 15. LIGHTING CONTROL ENGINEERING

Automatically calculate: fixture count, wattage, total electrical load, power supplies, driver requirements, circuit grouping, DMX universes, DMX addresses, cable lengths, voltage drop. Generate: lighting control schematic + fixture schedule + DMX map.

This should interface with AquaFlow rather than LuxuryForm rebuilding the complete fountain show-control system.

## 16. KINETIC / MOVING SCULPTURE ENGINE

Include even if implemented later. Support: rotation, linear movement, tilting, folding, opening, oscillation, cable movement, hydraulic movement.

Engineering: mass, inertia, acceleration, torque, motor power, gearbox ratio, bearing loads, shaft diameter, dynamic stress. Generate motion envelopes to detect collisions.

## 17. FABRICATION ENGINEERING

Where LuxuryForm becomes considerably more valuable than generic sculpture AI. Automatically convert artistic geometry into manufacturable geometry:

Outer artistic surface → internal structural skeleton → panel subdivision → fabrication components.

The system should propose: tubes, RHS, SHS, plates, ribs, frames, brackets, gussets.

## 18. PANELIZATION ENGINE

Complex surfaces automatically become manufacturable panels. Calculate: panel boundaries, plate dimensions, bending, rolling, forming, weld seams, tolerance, assembly sequence. Produce flat patterns for laser cutting, plasma cutting, waterjet, CNC — including DXF.

## 19. WELDING ENGINEERING

Generate: weld locations, weld type, weld length, weld size, accessibility, sequence, distortion considerations, grinding requirements, polishing requirements.

For stainless: fabrication → welding → grinding → polishing/passivation → final finish, as part of the manufacturing workflow.

## 20. INTERNAL SERVICES ROUTING

The AI must determine how utilities physically travel through the sculpture: water pipes/manifolds, power cables, DMX/data cables, motor/encoder/control wiring — with minimum bend radius, maintenance access, drainage, cable separation, waterproof penetrations.

## 21. MAINTENANCE ENGINEERING

Maintainability analysis for every sculpture: pump access, nozzle access, lighting replacement, internal access, drain points, inspection panels, electrical access, valve access, cleaning, corrosion inspection. AI should flag "component inaccessible after assembly."

## 22. FABRICATION SEQUENCE GENERATOR

Assembly strategy: Foundation → base frame → primary skeleton → secondary structure → internal pipework → electrical conduits → panels → welding → finishing → lighting → water equipment → testing → transport → site installation. Becomes a manufacturing method statement.

## 23. BOM ENGINE

Auto-generated categories: Metal (plate/tube/RHS), Hydraulic (pipes/nozzles/valves), Pumping (pumps/filters), Lighting (LEDs/drivers), Electrical (cables/panels), Control (DMX/PLC), Mechanical (bearings/motors), Installation (anchors/base plates). Every geometry modification updates the BOM.

## 24. COST ENGINE

Calculate: material, fabrication, CNC cutting, bending/forming, welding, polishing, hydraulic equipment, lighting, electrical, control, transport, installation, commissioning, overhead, contingency, margin. Produce estimated production cost AND recommended quotation.

## 25. AI ENGINEERING COPILOT

The AI understands the complete sculpture, not merely geometry. Example: "Make this sculpture 20% taller" → AI evaluates consequences (weight +31%, overturning +42%, base reinforcement, larger frame members, hydraulic head increase, lighting coverage change, cost increase) and offers a redesigned solution.

## 26. MULTI-AGENT DESIGN REVIEW

Separate internal AI reviewers:

- **Designer AI** — aesthetic quality
- **Structural AI** — stability and structural integrity
- **Hydraulic AI** — water system
- **Lighting AI** — illumination and effects
- **Fabrication AI** — manufacturability
- **Cost AI** — commercial viability
- **Chief Engineer AI** — resolves conflicts

Example: Designer says "reduce frame visibility"; Structural says "member reduction fails wind loading"; Chief Engineer: "replace 60×60×3 frame with 50×50×5 high-strength member and reposition internal bracing."

## 27. DESIGN OPTIMIZATION ENGINE

Goals: minimize weight / cost / panel count / weld length / pump power / energy — while maintaining aesthetics, structural safety, hydraulic effect, illumination, fabrication feasibility.

## 28. AUTOMATIC DESIGN GATES

Every project moves through mandatory gates:

- G0 — Brief Complete
- G1 — Concept Approved
- G2 — Geometry Valid
- G3 — Material Valid
- G4 — Structural PASS
- G5 — Hydraulic PASS
- G6 — Lighting PASS
- G7 — Fabrication PASS
- G8 — Maintainability PASS
- G9 — Cost PASS
- G10 — Production Package Approved

A failed engineering gate prevents the system from calling the model production ready.

## 29. OUTPUT / EXPORT SYSTEM

- **3D:** STEP, IGES, STL, OBJ, FBX, GLB/glTF, USD/USDZ
- **Manufacturing:** DXF, CNC files, flat patterns, panel drawings
- **Engineering:** structural calc report, hydraulic report, lighting report, electrical calculations, foundation design, equipment schedules
- **Documentation:** BOM, BOQ, quotation, fabrication methodology, installation methodology, maintenance manual
- **Drawings:** GA drawing, elevations, sections, fabrication drawings, weld drawings, hydraulic schematic, electrical schematic, lighting layout, foundation drawing

## 30. VISUALIZATION / CLIENT PRESENTATION

Day rendering, night rendering, 360° view, animation, water simulation, lighting simulation, kinetic simulation, site integration, AR/VR eventually. **One model drives engineering and presentation** — the render never drifts from what engineering is designing.

## 31. AQUAFLOW INTEGRATION

LuxuryForm owns **sculpture engineering**; AquaFlow owns **fountain/show control**.

Exchange — LuxuryForm → AquaFlow: fixture coordinates, nozzles, lights, valves, pumps, DMX devices, water zones, kinetic devices. AquaFlow returns: show programming/control information.

Do not duplicate AquaFlow inside LuxuryForm. Connect through defined interfaces.

## 32. LEARNING / KNOWLEDGE SYSTEM

Eventually connect with CogniNet. Store: previous sculpture geometry, calculations, materials, fabrication hours, actual costs, quotations, supplier prices, engineering failures, site problems, installation problems, client modifications, actual pump performance, lighting results.

Compare: Predicted → Designed → Fabricated → Installed → Actual performance — and improve future recommendations. The long-term competitive advantage.

---

## DEVELOPMENT AUDIT SCORECARD

Score every subsystem: 0 = nonexistent, 1 = concept only, 2 = prototype, 3 = functional, 4 = validated, 5 = production-grade.

| # | System | Weight |
|---|--------|--------|
| 1 | AI Concept Generation | 4% |
| 2 | Parametric Geometry | 7% |
| 3 | Geometry Integrity | 5% |
| 4 | Material Engineering | 4% |
| 5 | Structural Load Engine | 7% |
| 6 | Structural/FEA Analysis | 7% |
| 7 | Foundation/Anchors | 4% |
| 8 | Hydraulic Engineering | 7% |
| 9 | Water Simulation | 4% |
| 10 | Pump/Equipment Selection | 3% |
| 11 | Lighting Engineering | 5% |
| 12 | Lighting Simulation | 3% |
| 13 | Dynamic Lighting | 3% |
| 14 | Kinetic Engineering | 3% |
| 15 | Structural Skeleton Generator | 5% |
| 16 | Panelization | 4% |
| 17 | Welding Engineering | 3% |
| 18 | Internal Service Routing | 3% |
| 19 | Maintainability | 2% |
| 20 | Fabrication Sequencing | 2% |
| 21 | BOM | 3% |
| 22 | Cost/Quotation | 3% |
| 23 | Engineering AI Copilot | 4% |
| 24 | Multi-Agent Review | 2% |
| 25 | Optimization | 2% |
| 26 | CAD/Manufacturing Export | 4% |
| 27 | Engineering Documentation | 3% |
| 28 | Visualization | 2% |
| 29 | AquaFlow Integration | 2% |
| 30 | Learning/CogniNet Integration | 2% |

**Production threshold: 80%+ overall AND every safety-critical engineering gate ≥ 4/5.** A high overall score cannot compensate for weak structural, hydraulic, geometry-integrity, or fabrication validation.
