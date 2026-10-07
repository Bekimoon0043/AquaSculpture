import { useState } from 'react'
import { API_BASE_URL } from '../config'
import useBriefStore from '../store/briefStore'

// Engineering copilot (scope §25): "what if 20% taller?" — deterministic
// consequence diff from /api/copilot/scale.
export default function CopilotPanel() {
  const brief = useBriefStore((s) => s.brief)
  const [factor, setFactor] = useState(1.2)
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function run() {
    if (!brief) return
    setBusy(true)
    setError(null)
    try {
      const resp = await fetch(`${API_BASE_URL}/api/copilot/scale`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brief, factor }),
      })
      if (!resp.ok) throw new Error(`copilot failed: ${resp.status}`)
      setResult(await resp.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="panel">
      <h2>Engineering copilot</h2>
      <label style={{ color: 'var(--text-dim)' }}>
        Scale factor: <strong style={{ color: 'var(--text)' }}>{factor.toFixed(2)}×</strong>
        <input type="range" min="0.8" max="1.5" step="0.05" value={factor}
               style={{ width: '100%' }}
               onChange={(e) => setFactor(+e.target.value)} />
      </label>
      <button className="btn primary" onClick={run}
              disabled={!brief || busy}>
        {busy ? 'Analyzing…' : `What if ${Math.round(factor * 100 - 100)}% ${factor >= 1 ? 'bigger' : 'smaller'}?`}
      </button>
      {error && <p className="error">{error}</p>}
      {result && (
        <>
          <table>
            <thead><tr><th>Metric</th><th className="num">Now</th>
              <th className="num">Scaled</th><th className="num">Δ%</th></tr></thead>
            <tbody>
              {result.consequences.map((c) => (
                <tr key={c.metric}>
                  <td>{c.metric}</td>
                  <td className="num">{c.base}</td>
                  <td className="num">{c.scaled}</td>
                  <td className="num"
                      style={{ color: c.change_pct > 0 ? '#ffd166' : '#7bd88a' }}>
                    {c.change_pct > 0 ? '+' : ''}{c.change_pct}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {result.notes.map((n, i) => <p key={i} className="hint">• {n}</p>)}
        </>
      )}
    </div>
  )
}
