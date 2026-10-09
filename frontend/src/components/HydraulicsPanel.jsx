import useBriefStore from '../store/briefStore'

// Hydraulic network schematic (Depence "dependencies" lesson): the chain
// Basin -> Pump -> Filter -> Main -> Manifold -> Branch -> Valve -> Nozzle
// drawn as a dependency graph with flows and heads on the edges, instead of
// only schedules in tables. Scope §9 asks for exactly this network.
const W = 280

function Box({ x, y, w, h, title, lines, status }) {
  return (
    <g className={`hnode ${status || ''}`}>
      <rect x={x} y={y} width={w} height={h} rx={4} />
      <text x={x + 6} y={y + 12} className="hnode-title">{title}</text>
      {lines.map((l, i) => <text key={i} x={x + 6} y={y + 23 + i * 10} className="hnode-line">{l}</text>)}
    </g>
  )
}

function Edge({ x1, y1, x2, y2, label }) {
  const mx = (x1 + x2) / 2, my = (y1 + y2) / 2
  return (
    <g className="hedge">
      <line x1={x1} y1={y1} x2={x2} y2={y2} markerEnd="url(#arrow)" />
      {label && <text x={mx + 4} y={my + 3} className="hedge-label">{label}</text>}
    </g>
  )
}

const f1 = (v) => (v == null ? '—' : (+v).toFixed(1))
const f2 = (v) => (v == null ? '—' : (+v).toFixed(2))

export default function HydraulicsPanel() {
  const engineering = useBriefStore((s) => s.engineering)
  const stale = useBriefStore((s) => s.stale)
  const hyd = engineering?.hydraulics
  if (!hyd) {
    return <div className="panel"><h2>Water</h2><p className="hint">No run yet — press Generate.</p></div>
  }
  const basin = engineering.basin?.metadata
  const duty = hyd.duty_point || {}
  const filt = hyd.filtration
  const main = hyd.main_pipe
  const man = hyd.manifold
  const branches = hyd.features.filter((f) => f.flow_lps > 0)
  const nozzles = Object.fromEntries((hyd.schedules?.nozzles || []).map((n) => [n.type, n]))
  const pump = hyd.schedules?.pump

  // Layout: trunk column on the left, branches stacked on the right.
  const trunk = [
    { title: 'BASIN', lines: basin ? [`${f1(basin.water_volume_m3)} m³ · turnover ${f1(hyd.turnover_min)} min`] : ['no basin'] },
    { title: 'PUMP', lines: [`${f2(hyd.motor_kw)} kW motor · η ${hyd.pump_efficiency}`,
                              `duty ${f1(duty.duty_flow_lps)} L/s @ ${f1(duty.duty_head_m)} m`],
      status: duty.duty_ok === false ? 'bad' : 'ok' },
    ...(filt ? [{ title: 'FILTER', lines: [`${filt.type} · ${filt.filter_area_m2} m²`, `${filt.flow_m3h} m³/h`] }] : []),
    ...(main ? [{ title: 'MAIN', lines: [`DN${main.dn} · ${f2(main.velocity_ms)} m/s`, `${hyd.pipe_length_m} m run`],
                  status: main.velocity_ms > 2.5 ? 'warn' : '' }] : []),
    ...(man ? [{ title: 'MANIFOLD', lines: [`DN${man.dn} · ${man.branches} branches`] }] : []),
  ]
  const bh = 36, gap = 22, bx = 8, bw = 128
  const trunkY = (i) => 10 + i * (bh + gap)
  const edgeLabels = [
    `+${f1(hyd.static_lift_m)} m static`,
    `${f1(hyd.total_flow_lps)} L/s`,
    `−${f2(hyd.friction_head_m)} m friction`,
    `−${f2(hyd.worst_branch_loss_m)} m worst branch`,
  ]
  const rx = 152, rw = 120, rh = 44
  const branchY = (i) => 10 + i * (rh + 10)
  const manifoldIdx = trunk.length - 1
  const height = Math.max(trunkY(trunk.length - 1) + bh, branchY(branches.length - 1) + rh) + 12

  return (
    <div className={`panel ${stale ? 'stale' : ''}`}>
      <div className="panel-head"><h2>Water · hydraulic network</h2>{stale && <span className="hint">updating…</span>}</div>
      <svg className="hydro" viewBox={`0 0 ${W} ${height}`} width="100%">
        <defs>
          <marker id="arrow" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="5" markerHeight="5" orient="auto">
            <path d="M0,0 L6,3 L0,6 z" />
          </marker>
        </defs>
        {trunk.map((n, i) => (
          <g key={n.title}>
            <Box x={bx} y={trunkY(i)} w={bw} h={bh} {...n} />
            {i < trunk.length - 1 && (
              <Edge x1={bx + bw / 2} y1={trunkY(i) + bh} x2={bx + bw / 2} y2={trunkY(i + 1)} label={edgeLabels[i]} />
            )}
          </g>
        ))}
        {branches.map((f, i) => {
          const nz = nozzles[f.type]
          const lines = [
            `DN${f.pipe?.dn ?? '—'} · ${f1(f.flow_lps)} L/s · ${f.valve?.type || 'valve'}`,
            `loss ${f2(f.branch_loss_m)} m`,
            nz ? `${nz.count} × ${nz.nozzle}` : f.jet_height_m ? `jet ${f1(f.jet_height_m)} m` : `head ${f2(f.pressure_head_m)} m`,
          ]
          return (
            <g key={f.type}>
              <Edge x1={bx + bw} y1={trunkY(manifoldIdx) + bh / 2} x2={rx} y2={branchY(i) + rh / 2} />
              <Box x={rx} y={branchY(i)} w={rw} h={rh} title={f.type.replace(/_/g, ' ')} lines={lines} />
            </g>
          )
        })}
      </svg>
      <div className="tdh">
        <span>TDH</span>
        <span>{f1(hyd.static_lift_m)} static + {f2(hyd.friction_head_m)} main + {f2(hyd.worst_branch_loss_m)} branch + {f1(hyd.nozzle_pressure_head_m)} nozzle</span>
        <strong>= {f1(hyd.tdh_m)} m</strong>
      </div>
      {duty.pump_class && (
        <p className="hint">
          Pump {duty.pump_class}: shut-off {f1(duty.shutoff_head_m)} m, run-out {f1(duty.runout_flow_lps)} L/s, flow margin {f1(duty.flow_margin_pct)}%
          {duty.upsize_count ? ` (auto-upsized ${duty.upsize_count}×)` : ''}{duty.duty_ok === false ? ' — DUTY POINT NOT MET' : ''}
        </p>
      )}

      {hyd.schedules?.pipes && (
        <>
          <h3 className="form-section">Pipe schedule</h3>
          <table><thead><tr><th>Run</th><th className="num">DN</th><th className="num">m/s</th><th className="num">m</th></tr></thead>
            <tbody>{hyd.schedules.pipes.map((p, i) => (
              <tr key={i}><td>{p.run}</td><td className="num">{p.dn}</td><td className="num">{f2(p.velocity_ms)}</td><td className="num">{f1(p.length_m)}</td></tr>
            ))}</tbody></table>
        </>
      )}
      {hyd.schedules?.valves?.length > 0 && (
        <>
          <h3 className="form-section">Valve schedule</h3>
          <table><thead><tr><th>Branch</th><th className="num">DN</th><th>Type</th></tr></thead>
            <tbody>{hyd.schedules.valves.map((v, i) => (
              <tr key={i}><td>{v.branch}</td><td className="num">{v.dn}</td><td>{v.type}</td></tr>
            ))}</tbody></table>
        </>
      )}
      {hyd.schedules?.nozzles?.length > 0 && (
        <>
          <h3 className="form-section">Nozzle schedule</h3>
          <table><thead><tr><th>Feature</th><th>Nozzle</th><th className="num">n</th><th className="num">L/s</th></tr></thead>
            <tbody>{hyd.schedules.nozzles.map((n, i) => (
              <tr key={i}><td>{n.type}</td><td>{n.nozzle}</td><td className="num">{n.count}</td><td className="num">{f1(n.flow_lps)}</td></tr>
            ))}</tbody></table>
        </>
      )}
      {pump && (
        <>
          <h3 className="form-section">Pump</h3>
          <table><tbody>{Object.entries(pump).map(([k, v]) => (
            <tr key={k}><td>{k.replace(/_/g, ' ')}</td><td className="num">{typeof v === 'number' ? (Number.isInteger(v) ? v : v.toFixed(2)) : String(v)}</td></tr>
          ))}</tbody></table>
        </>
      )}
      {hyd.wind_drift?.zones?.length > 0 && (
        <p className="hint">Wind drift: {hyd.wind_drift.zones.length} exclusion zone(s) computed — see viewport splash zones.</p>
      )}
    </div>
  )
}
