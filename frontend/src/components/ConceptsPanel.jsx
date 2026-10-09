import { useState } from 'react'
import { API_BASE_URL } from '../config'
import useBriefStore from '../store/briefStore'

// Concept explorer (Fusion Generative Design lesson): outcomes on a scatter
// (cost vs weight, coloured by gate verdict), cards, a two-up compare table,
// the Pareto front from /api/optimize overlaid, and "Approve" which records
// the G1 human gate in the brief.
const METRICS = [
  { key: 'total_usd', label: 'Total cost', unit: 'USD', lower: true, fmt: (v) => Math.round(v).toLocaleString() },
  { key: 'mass_kg', label: 'Shell mass', unit: 'kg', lower: true, fmt: (v) => v.toFixed(0) },
  { key: 'steel_kg', label: 'Skeleton steel', unit: 'kg', lower: true, fmt: (v) => v.toFixed(0) },
  { key: 'base_moment_knm', label: 'Base moment', unit: 'kN·m', lower: true, fmt: (v) => v.toFixed(1) },
  { key: 'deflection_mm', label: 'Deflection', unit: 'mm', lower: true, fmt: (v) => v.toFixed(1) },
  { key: 'pump_kw', label: 'Pump', unit: 'kW', lower: true, fmt: (v) => v.toFixed(2) },
  { key: 'lux_coverage_pct', label: 'Lit coverage', unit: '%', lower: false, fmt: (v) => v.toFixed(0) },
  { key: 'panels', label: 'Panels', unit: '', lower: true, fmt: (v) => String(v) },
  { key: 'weld_m', label: 'Weld seam', unit: 'm', lower: true, fmt: (v) => v.toFixed(1) },
]

const weight = (h) => (h.mass_kg || 0) + (h.steel_kg || 0)

function Scatter({ points, front, selected, onPick }) {
  const W = 268, H = 150, P = { l: 38, r: 8, t: 8, b: 22 }
  const all = [...points, ...front.map((f) => ({ x: f.cost, y: f.weight }))]
  if (all.length === 0) return null
  const xs = all.map((p) => p.x), ys = all.map((p) => p.y)
  const x0 = Math.min(...xs) * 0.95, x1 = Math.max(...xs) * 1.05 || 1
  const y0 = Math.min(...ys) * 0.95, y1 = Math.max(...ys) * 1.05 || 1
  const sx = (v) => P.l + ((v - x0) / (x1 - x0 || 1)) * (W - P.l - P.r)
  const sy = (v) => H - P.b - ((v - y0) / (y1 - y0 || 1)) * (H - P.t - P.b)
  const frontPath = front.length > 1
    ? front.map((f, i) => `${i ? 'L' : 'M'}${sx(f.cost).toFixed(1)},${sy(f.weight).toFixed(1)}`).join(' ')
    : null
  return (
    <svg className="scatter" viewBox={`0 0 ${W} ${H}`} width="100%">
      <line x1={P.l} y1={H - P.b} x2={W - P.r} y2={H - P.b} className="axis" />
      <line x1={P.l} y1={P.t} x2={P.l} y2={H - P.b} className="axis" />
      <text x={(W + P.l) / 2} y={H - 6} className="axis-label">cost (USD)</text>
      <text x={10} y={(H - P.b) / 2} className="axis-label" transform={`rotate(-90 10 ${(H - P.b) / 2})`}>weight (kg)</text>
      <text x={P.l - 3} y={H - P.b + 3} className="tick" textAnchor="end">{Math.round(y0 / 100) * 100}</text>
      <text x={P.l - 3} y={P.t + 8} className="tick" textAnchor="end">{Math.round(y1 / 100) * 100}</text>
      <text x={P.l} y={H - P.b + 11} className="tick">{Math.round(x0 / 1000)}k</text>
      <text x={W - P.r} y={H - P.b + 11} className="tick" textAnchor="end">{Math.round(x1 / 1000)}k</text>
      {frontPath && <path d={frontPath} className="front" />}
      {front.map((f, i) => (
        <circle key={`f${i}`} cx={sx(f.cost)} cy={sy(f.weight)} r={2.6} className="front-dot">
          <title>{`Pareto: scale ${f.scale}×, section ${Math.round(f.section_shave * 100)}% — $${Math.round(f.cost).toLocaleString()}, ${f.weight} kg`}</title>
        </circle>
      ))}
      {points.map((p) => (
        <circle key={p.id} cx={sx(p.x)} cy={sy(p.y)} r={selected.includes(p.id) ? 6 : 4.5}
                className={`dot ${p.pass ? 'pass' : 'fail'} ${selected.includes(p.id) ? 'sel' : ''}`}
                onClick={() => onPick(p.id)}>
          <title>{`${p.label} — $${Math.round(p.x).toLocaleString()}, ${Math.round(p.y)} kg, gates ${p.pass ? 'PASS' : 'FAIL'}`}</title>
        </circle>
      ))}
    </svg>
  )
}

function Compare({ a, b }) {
  return (
    <table className="compare">
      <thead><tr><th>Metric</th><th className="num">{a.theme}</th><th className="num">{b.theme}</th></tr></thead>
      <tbody>
        {METRICS.map((m) => {
          const va = a.headline[m.key], vb = b.headline[m.key]
          if (va == null || vb == null) return null
          const aBetter = va !== vb && (m.lower ? va < vb : va > vb)
          const bBetter = va !== vb && !aBetter
          return (
            <tr key={m.key}>
              <td>{m.label}{m.unit ? <span className="hint"> {m.unit}</span> : null}</td>
              <td className={`num ${aBetter ? 'better' : ''}`}>{m.fmt(va)}</td>
              <td className={`num ${bBetter ? 'better' : ''}`}>{m.fmt(vb)}</td>
            </tr>
          )
        })}
        <tr>
          <td>Gates</td>
          <td className={`num ${a.headline.gates_pass ? 'better' : 'worse'}`}>{a.headline.gates_pass ? 'PASS' : 'FAIL'}</td>
          <td className={`num ${b.headline.gates_pass ? 'better' : 'worse'}`}>{b.headline.gates_pass ? 'PASS' : 'FAIL'}</td>
        </tr>
      </tbody>
    </table>
  )
}

export default function ConceptsPanel() {
  const brief = useBriefStore((s) => s.brief)
  const engineering = useBriefStore((s) => s.engineering)
  const setBrief = useBriefStore((s) => s.setBrief)
  const setLoading = useBriefStore((s) => s.setLoading)
  const runEngineering = useBriefStore((s) => s._runEngineering)
  const approve = useBriefStore((s) => s.approve)
  const approver = useBriefStore((s) => s.approver)
  const setApprover = useBriefStore((s) => s.setApprover)
  const [concepts, setConcepts] = useState(null)
  const [front, setFront] = useState([])
  const [selected, setSelected] = useState([])
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)

  const g1 = brief?.approvals?.G1

  async function call(path, body) {
    const resp = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!resp.ok) throw new Error(`${path} failed: ${resp.status}`)
    return resp.json()
  }

  async function generate() {
    setBusy('concepts'); setError(null); setSelected([]); setFront([])
    try {
      const base = brief || await (await fetch(`${API_BASE_URL}/api/brief/example`)).json()
      const data = await call('/api/concepts', { brief: base, count: 4 })
      setConcepts(data.concepts.map((c, i) => ({ ...c, id: `c${i}` })))
    } catch (e) { setError(e.message) } finally { setBusy(null) }
  }

  async function pareto() {
    if (!brief) return
    setBusy('pareto'); setError(null)
    try {
      const data = await call('/api/optimize', { brief, goal: 'pareto' })
      setFront(data.front || [])
      if (!data.front?.length) setError('No gate-passing, in-budget variant on the scale × section grid.')
    } catch (e) { setError(e.message) } finally { setBusy(null) }
  }

  async function load(c) {
    setLoading()
    setBrief(c.brief)
    await runEngineering(c.brief)
  }

  function pick(id) {
    setSelected((s) => s.includes(id) ? s.filter((x) => x !== id) : [...s.slice(-1), id])
  }

  const points = (concepts || []).map((c) => ({
    id: c.id, label: c.theme, x: c.headline.total_usd, y: weight(c.headline),
    pass: c.headline.gates_pass,
  }))
  const pair = selected.map((id) => concepts?.find((c) => c.id === id)).filter(Boolean)

  return (
    <div className="panel">
      <div className="panel-head">
        <h2>Concept explorer</h2>
        {concepts && (
          <button className="btn mini" onClick={pareto} disabled={!brief || !!busy} title="Pareto front: cost vs weight over scale × section variants of the current brief; gate-failing variants are rejected">
            {busy === 'pareto' ? 'Searching…' : 'Pareto'}
          </button>
        )}
      </div>
      <button className="btn primary" onClick={generate} disabled={!!busy}>
        {busy === 'concepts' ? 'Engineering 4 concepts…' : concepts ? 'Regenerate 4 concepts' : 'Generate 4 concepts'}
      </button>
      {error && <p className="error">{error}</p>}

      {concepts && (
        <>
          <Scatter points={points} front={front} selected={selected} onPick={pick} />
          <p className="hint">Click two dots (or cards) to compare. Green = all gates pass; red = an engineering gate fails.{front.length ? ' Gold line = Pareto front of the current design.' : ''}</p>
          {pair.length === 2 && <Compare a={pair[0]} b={pair[1]} />}
          <div className="concept-grid">
            {concepts.map((c) => (
              <div key={c.id} className={`concept-card ${selected.includes(c.id) ? 'sel' : ''}`} onClick={() => pick(c.id)}>
                <div className="concept-head">
                  <strong>{c.theme}</strong>
                  <span className={c.headline.gates_pass ? 'ok' : 'bad'}>{c.headline.gates_pass ? 'PASS' : 'FAIL'}</span>
                </div>
                <div className="hint">{c.brief.sculpture.family} · {c.brief.sculpture.material} · {c.brief.sculpture.finish}</div>
                <div className="concept-metrics">
                  <span>{Math.round(c.headline.mass_kg + c.headline.steel_kg)} kg</span>
                  <span>${Math.round(c.headline.total_usd).toLocaleString()}</span>
                  <span>{c.headline.pump_kw.toFixed(1)} kW</span>
                  <span>{c.headline.panels} panels</span>
                </div>
                <button className="btn mini" onClick={(e) => { e.stopPropagation(); load(c) }}>
                  Load into engineering
                </button>
              </div>
            ))}
          </div>
        </>
      )}

      <h3 className="form-section">G1 · Concept approval</h3>
      {g1 ? (
        <div className="approval ok">
          Approved by <strong>{g1.by}</strong> on {g1.at.slice(0, 10)}{g1.note ? ` — ${g1.note}` : ''}
          <button className="btn mini" onClick={() => approve('G1', null)}>Revoke</button>
        </div>
      ) : (
        <div className="approval">
          <input type="text" placeholder="approver" value={approver} onChange={(e) => setApprover(e.target.value)} />
          <button className="btn" disabled={!brief || !engineering || !approver.trim()}
                  onClick={() => approve('G1', { by: approver.trim(), note: `concept: ${brief?.sculpture?.family}` })}
                  title="Record human approval of the current concept; G1 turns green and the approval is saved in the brief">
            Approve current concept
          </button>
        </div>
      )}
      <p className="hint">Every concept is fully engineered — not a random image. Approval is recorded in the brief and voided automatically if you change family.</p>
    </div>
  )
}
