import useBriefStore from '../store/briefStore'

// KPI strip (Forma/TestFit lesson): the headline numbers, each with its
// delta vs the previous run, so every edit's consequence is visible at once.
const KPIS = [
  { key: 'mass', label: 'Shell mass', unit: 'kg', lowerIsBetter: true,
    get: (e) => e.sculpture.metadata.mass_kg, fmt: (v) => v.toFixed(0) },
  { key: 'moment', label: 'Base moment', unit: 'kN·m', lowerIsBetter: true,
    get: (e) => e.structural?.total_base_moment_knm, fmt: (v) => v.toFixed(1) },
  { key: 'defl', label: 'Deflection', unit: 'mm', lowerIsBetter: true,
    get: (e) => e.structural?.analysis?.deflection_mm, fmt: (v) => v.toFixed(1) },
  { key: 'pump', label: 'Pump', unit: 'kW', lowerIsBetter: true,
    get: (e) => e.hydraulics?.motor_kw, fmt: (v) => v.toFixed(2) },
  { key: 'lux', label: 'Lit coverage', unit: '%', lowerIsBetter: false,
    get: (e) => e.lighting?.illumination?.coverage_pct, fmt: (v) => v.toFixed(0) },
  { key: 'cost', label: 'Total cost', unit: 'USD', lowerIsBetter: true,
    get: (e) => e.cost?.total_usd, fmt: (v) => Math.round(v).toLocaleString() },
  { key: 'gates', label: 'Gates passed', unit: '', lowerIsBetter: false,
    get: (e) => e.gates?.gates?.filter((g) => g.status === 'pass').length,
    fmt: (v) => `${v}/11` },
]

function Kpi({ def, now, prev }) {
  const v = def.get(now)
  const p = prev ? def.get(prev) : undefined
  if (v == null) return null
  let delta = null
  if (p != null && p !== v) {
    const pct = p ? ((v - p) / Math.abs(p)) * 100 : null
    const good = def.lowerIsBetter ? v < p : v > p
    delta = {
      text: pct != null && Math.abs(pct) >= 0.05
        ? `${pct > 0 ? '+' : ''}${pct.toFixed(Math.abs(pct) < 10 ? 1 : 0)}%`
        : `${v > p ? '+' : ''}${def.fmt(v - p)}`,
      cls: good ? 'up' : 'down',
    }
  }
  return (
    <div className="kpi" title={`${def.label}${p != null ? ` — previous ${def.fmt(p)} ${def.unit}` : ''}`}>
      <span className="kpi-label">{def.label}</span>
      <span className="kpi-value">{def.fmt(v)}<small>{def.unit}</small></span>
      <span className={`kpi-delta ${delta ? delta.cls : 'neutral'}`}>{delta ? delta.text : '—'}</span>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div style={styles.row}>
      <span style={styles.label}>{label}</span>
      <span>{value}</span>
    </div>
  )
}

export default function EngineeringPanel() {
  const engineering = useBriefStore((s) => s.engineering)
  const prev = useBriefStore((s) => s.prevEngineering)
  const stale = useBriefStore((s) => s.stale)
  if (!engineering) {
    return <div style={styles.panel}><h2 style={styles.heading}>Engineering</h2>
      <p style={styles.empty}>No run yet — press Generate.</p></div>
  }

  const geo = engineering.geo_quantities
  const hyd = engineering.hydraulics
  const meta = engineering.sculpture.metadata
  const basin = engineering.basin?.metadata
  const struct = engineering.structural
  const gates = engineering.gates
  const light = engineering.lighting

  return (
    <div style={styles.panel} className={stale ? 'stale' : ''}>
      <div className="panel-head">
        <h2 style={styles.heading}>Engineering</h2>
        {stale && <span className="hint">updating…</span>}
      </div>
      <div className="kpi-grid">
        {KPIS.map((d) => <Kpi key={d.key} def={d} now={engineering} prev={prev} />)}
      </div>
      {gates && (
        <>
          <h3 style={styles.sub}>Design gates</h3>
          <div style={styles.gateGrid}>
            {gates.gates.map((g) => (
              <span key={g.id} style={{ ...styles.gate, ...gateStyle(g.status) }}
                    title={`${g.label}${g.note ? ' — ' + g.note : ''}`}>
                {g.id}
              </span>
            ))}
          </div>
          <Row label="Production ready"
               value={gates.production_ready ? 'YES' : gates.hard_fail ? 'NO — gate failure' : 'NO — pending gates'} />
        </>
      )}
      <h3 style={styles.sub}>Geometry</h3>
      <Row label="Surface area" value={`${geo.surface_area_m2.toFixed(2)} m²`} />
      <Row label="Swept volume" value={`${geo.volume_m3.toFixed(3)} m³`} />
      <Row label="Shell thickness" value={`${(meta.shell_thickness_m * 1000).toFixed(1)} mm`} />
      <Row label="Shell mass" value={`${meta.mass_kg.toFixed(1)} kg`} />
      <Row label="Bounding box" value={geo.bounding_box.size.map((v) => v.toFixed(2)).join(' × ') + ' m'} />
      <Row label="CoG" value={geo.center_of_gravity_m.map((v) => v.toFixed(2)).join(', ') + ' m'} />
      {basin && (
        <>
          <h3 style={styles.sub}>Basin</h3>
          <Row label="Water volume" value={`${basin.water_volume_m3.toFixed(2)} m³`} />
          <Row label="Wetted area" value={`${basin.wetted_area_m2.toFixed(2)} m²`} />
          {basin.weir_length_m && <Row label="Perimeter weir" value={`${basin.weir_length_m.toFixed(2)} m`} />}
        </>
      )}
      <h3 style={styles.sub}>Hydraulics</h3>
      {hyd.features.map((f, i) => (
        <Row key={i} label={f.type} value={`${f.flow_lps.toFixed(2)} L/s`} />
      ))}
      <Row label="Total flow" value={`${hyd.total_flow_lps.toFixed(2)} L/s`} />
      <Row label="TDH" value={`${hyd.tdh_m.toFixed(2)} m`} />
      {hyd.main_pipe && <Row label="Main pipe" value={`DN${hyd.main_pipe.dn} @ ${hyd.main_pipe.velocity_ms.toFixed(2)} m/s`} />}
      <Row label="Pump motor" value={`${hyd.motor_kw.toFixed(2)} kW`} />
      {hyd.turnover_min && <Row label="Turnover" value={`${hyd.turnover_min.toFixed(1)} min`} />}
      {struct && (
        <>
          <h3 style={styles.sub}>Structural</h3>
          <Row label="Wind / jet / seismic" value={`${struct.loads.wind_kn.toFixed(2)} / ${struct.loads.jet_reaction_kn.toFixed(2)} / ${struct.loads.seismic_kn.toFixed(2)} kN`} />
          <Row label="Deflection" value={`${struct.analysis.deflection_mm.toFixed(1)} mm (limit ${struct.analysis.deflection_limit_mm.toFixed(0)})`} />
          <Row label="Natural freq" value={`${struct.analysis.natural_frequency_hz.toFixed(2)} Hz${struct.analysis.resonance_risk ? ' — RESONANCE RISK' : ''}`} />
          {struct.fea && !struct.fea.error && (
            <Row label="FEA frame" value={`${struct.fea.section} · ${struct.fea.max_stress_mpa} MPa · ${struct.fea.max_displacement_mm} mm`} />
          )}
          <Row label="Safety factors" value={Object.entries(struct.safety_factors)
            .filter(([k]) => !['required', 'all_pass', 'anchored'].includes(k))
            .map(([k, v]) => `${k} ${v ?? 'n/a'}`).join(' · ')} />
        </>
      )}
      {light?.controls && (
        <>
          <h3 style={styles.sub}>Lighting</h3>
          <Row label="Fixtures" value={`${light.controls.fixture_count} · ${light.controls.total_load_w.toFixed(0)} W`} />
          <Row label="PSU / DMX" value={`${light.controls.psu_count} × ${light.controls.psu_wattage} W · ${light.controls.dmx_universes} universe(s), ${light.controls.dmx_channels_used} ch`} />
          <Row label="Worst voltage drop" value={`${light.controls.max_voltage_drop_v} V${light.controls.voltage_drop_ok ? '' : ' — OVER LIMIT'}`} />
          {light.illumination && (
            <Row label="Illumination" value={`${light.illumination.avg_lux} lux avg · ${light.illumination.coverage_pct}% ≥ ${light.illumination.min_lux_target} lux`} />
          )}
        </>
      )}
    </div>
  )
}

function gateStyle(status) {
  switch (status) {
    case 'pass': return { background: '#1e4620', color: '#7fb285' }
    case 'warning': return { background: '#4a3b14', color: '#c9a86a' }
    case 'fail': return { background: '#4a1a1a', color: '#d08a8a' }
    default: return { background: '#262a32', color: '#666' }
  }
}

const styles = {
  panel: { padding: '12px', overflow: 'auto' },
  heading: { margin: 0, fontSize: '11px', color: '#8b96a3', textTransform: 'uppercase', letterSpacing: '1px' },
  sub: { margin: '8px 0 2px', fontSize: '10px', color: '#8b96a3', textTransform: 'uppercase', letterSpacing: '1px' },
  row: { display: 'flex', justifyContent: 'space-between', fontSize: '13px', padding: '2px 0', gap: '8px' },
  label: { color: '#999', flexShrink: 0 },
  empty: { color: '#666', fontSize: '13px' },
  gateGrid: { display: 'flex', flexWrap: 'wrap', gap: '4px' },
  gate: { padding: '2px 8px', borderRadius: '3px', fontSize: '11px', fontWeight: 700, cursor: 'default' },
}
