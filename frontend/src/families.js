// Family labels + house defaults (portfolio-tuned). Parameter schemas —
// types, ranges, choices — come from /api/geometry/families; these defaults
// overlay the generator signature defaults (see briefStore.familyDefaults).
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
  stacked_c_rings: {
    label: 'Stacked C-Rings (Fountain)',  // §3 brief alias of stacked_rings
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
  standing_figure: {
    label: 'Standing Figure / Liberty (Figurative)',
    defaults: { height_m: 6.0, pedestal: true, pedestal_ratio: 0.3, crown_rays: 7, drapery_folds: 9 },
  },
  torus_knot: {
    label: 'Torus Knot',
    defaults: { p: 2, q: 3, major_radius_m: 1.4, tube_radius_m: 0.16 },
  },
  mobius_ribbon: {
    label: 'Möbius Ribbon',
    defaults: { radius_m: 1.2, width_m: 0.5, thickness_m: 0.05 },
  },
  wave_surface: {
    label: 'Wave Wall',
    defaults: { width_m: 3.0, height_m: 2.5, waves: 3, amplitude_m: 0.35 },
  },
  spiral_column: {
    label: 'Spiral Column',
    defaults: { height_m: 3.0, radius_m: 0.8, turns: 3.0, tube_radius_m: 0.12 },
  },
  geodesic_shell: {
    label: 'Geodesic Shell',
    defaults: { diameter_m: 3.0, subdivisions: 2 },
  },
}
