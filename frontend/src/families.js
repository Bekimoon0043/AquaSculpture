export const FAMILIES = {
  open_ring: {
    label: 'Open Ring / Crescent',
    defaults: { diameter_m: 4.0, tube_radius_m: 0.15, opening_deg: 90, segments: 48 },
  },
  twisted_torus: {
    label: 'Twisted Torus (Organic Void)',
    defaults: { major_radius_m: 1.9, section_width_m: 0.45, section_depth_m: 0.28, twist_count: 2, morph: 0.55, aspect_xy: 0.61 },
  },
  ribbon_knot: {
    label: 'Ribbon Knot / Flame',
    defaults: { height_m: 4.0, preset: 'figure_eight', width_m: 0.6, thickness_m: 0.08, twist_deg: 180 },
  },
  organic_flame: {
    label: 'Organic Flame',
    defaults: { height_m: 4.0, lobe_count: 4, spill_lips: true },
  },
  stacked_rings: {
    label: 'Stacked Rings (Totem)',
    defaults: {},
  },
  crescent_inner: {
    label: 'Crescent + Inner Figure',
    defaults: { diameter_m: 2.4, opening_deg: 90, inner_shape: 'bird' },
  },
  arc_fin_array: {
    label: 'Arc-Fin Array',
    defaults: { fin_count: 8, height_m: 3.0, arc_radius_m: 4.0, layout_diameter_m: 3.0 },
  },
  relief_panel: {
    label: 'Relief Panel',
    defaults: {},
  },
  buddha_seated: {
    label: 'Seated Buddha (Figurative)',
    defaults: { height_m: 2.0, pedestal: true },
  },
}
