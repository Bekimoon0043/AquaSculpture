"""STEP (AP214, faceted BREP) export — dependency-free, scope §29.

Emits ISO-10303-21 text: one CARTESIAN_POINT per vertex, one FACE per
triangle (POLY_LOOP + FACE_OUTER_BOUND), wrapped in CLOSED_SHELL ->
MANIFOLD_SOLID_BREP with SI-metre units and full context boilerplate.

v1: faceted geometry only (no NURBS). Verified structurally in tests;
import verification in a CAD kernel is a manual QA step.
"""

from datetime import datetime, timezone

HEADER = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Sculpture shell, faceted BREP'),'2;1');
FILE_NAME('%s','%s',('LuxuryForm Studio'),('LuxuryForm Studio'),
  'LuxuryForm','LuxuryForm','');
FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 3 1 1 }'));
ENDSEC;
DATA;
/* units + context */
#1 = ( LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT($,.METRE.) );
#2 = ( NAMED_UNIT(*) PLANE_ANGLE_UNIT() SI_UNIT($,.RADIAN.) );
#3 = ( NAMED_UNIT(*) SI_UNIT($,.STERADIAN.) SOLID_ANGLE_UNIT() );
#4 = UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(0.001),#1,
  'distance_accuracy_value','');
#5 = ( GEOMETRIC_REPRESENTATION_CONTEXT(3)
  GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#4))
  GLOBAL_UNIT_ASSIGNED_CONTEXT((#1,#2,#3)) REPRESENTATION_CONTEXT('','3D') );
#6 = AXIS2_PLACEMENT_3D('',#7,#8,#9);
#7 = CARTESIAN_POINT('',(0.,0.,0.));
#8 = DIRECTION('',(0.,0.,1.));
#9 = DIRECTION('',(1.,0.,0.));
"""

FOOTER = """ENDSEC;
END-ISO-10303-21;
"""


def build_step(vertices, faces, name: str = "sculpture") -> str:
    lines = [HEADER % (name,
                       datetime.now(timezone.utc).isoformat(timespec="seconds"))]
    eid = 10
    point_ids = []
    for x, y, z in vertices:
        lines.append(f"#{eid} = CARTESIAN_POINT('',({x:.6f},{y:.6f},{z:.6f}));\n")
        point_ids.append(eid)
        eid += 1
    face_ids = []
    for a, b, c in faces:
        loop_id, bound_id, face_id = eid, eid + 1, eid + 2
        lines.append(f"#{loop_id} = POLY_LOOP('',(#{point_ids[a]},"
                     f"#{point_ids[b]},#{point_ids[c]}));\n")
        lines.append(f"#{bound_id} = FACE_OUTER_BOUND('',#{loop_id},.T.);\n")
        lines.append(f"#{face_id} = FACE('',(#{bound_id}));\n")
        face_ids.append(face_id)
        eid += 3
    shell_id = eid
    brep_id = eid + 1
    shape_id = eid + 2
    refs = ",".join(f"#{f}" for f in face_ids)
    lines.append(f"#{shell_id} = CLOSED_SHELL('',({refs}));\n")
    lines.append(f"#{brep_id} = MANIFOLD_SOLID_BREP('{name}',#{shell_id});\n")
    lines.append(f"#{shape_id} = SHAPE_DEFINITION_REPRESENTATION(#999,#{eid + 3});\n")
    lines.append(f"#{eid + 3} = ADVANCED_BREP_SHAPE_REPRESENTATION('{name}',"
                 f"(#{brep_id},#6),#5);\n")
    lines.append("#999 = PRODUCT_DEFINITION_SHAPE('','',#998);\n")
    lines.append("#998 = PRODUCT_DEFINITION('','',#997,#996);\n")
    lines.append("#997 = PRODUCT_DEFINITION_FORMATION('','',#995);\n")
    lines.append(f"#995 = PRODUCT('{name}','{name}','',(#994));\n")
    lines.append("#994 = PRODUCT_CONTEXT('',#993,'mechanical');\n")
    lines.append("#993 = APPLICATION_CONTEXT('automotive design');\n")
    lines.append(FOOTER)
    return "".join(lines)


def step_bytes(vertices, faces, name: str = "sculpture") -> bytes:
    return build_step(vertices, faces, name).encode("ascii", errors="replace")
