import useBriefStore from '../store/briefStore'

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

  return (
    <div style={styles.panel}>
      <h2 style={styles.heading}>Engineering</h2>
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
          <Row label="Safety factors" value={Object.entries(struct.safety_factors)
            .filter(([k]) => !['required', 'all_pass', 'anchored'].includes(k))
            .map(([k, v]) => `${k} ${v ?? 'n/a'}`).join(' · ')} />
        </>
      )}
    </div>
  )
}

function gateStyle(status) {
  switch (status) {
    case 'pass': return { background: '#1e4620', color: '#7bd88a' }
    case 'warning': return { background: '#4a3b14', color: '#ffd166' }
    case 'fail': return { background: '#4a1a1a', color: '#ff6b6b' }
    default: return { background: '#262a32', color: '#666' }
  }
}

const styles = {
  panel: { padding: '12px', overflow: 'auto' },
  heading: { margin: 0, fontSize: '14px', color: '#ccc', textTransform: 'uppercase' },
  sub: { margin: '10px 0 4px', fontSize: '12px', color: '#7da7ff', textTransform: 'uppercase' },
  row: { display: 'flex', justifyContent: 'space-between', fontSize: '13px', padding: '2px 0', gap: '8px' },
  label: { color: '#999', flexShrink: 0 },
  empty: { color: '#666', fontSize: '13px' },
  gateGrid: { display: 'flex', flexWrap: 'wrap', gap: '4px' },
  gate: { padding: '2px 8px', borderRadius: '3px', fontSize: '11px', fontWeight: 700, cursor: 'default' },
}
