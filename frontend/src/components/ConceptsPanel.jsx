import { useState } from 'react'
import { API_BASE_URL } from '../config'
import useBriefStore from '../store/briefStore'

// Multi-concept generator (scope §2.2): controlled design families, each
// delivered with engineering + cost already attached.
export default function ConceptsPanel() {
  const { brief, setBrief, setEngineering, setLoading, setError } = useBriefStore()
  const [concepts, setConcepts] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setErrorLocal] = useState(null)

  async function generate() {
    setBusy(true)
    setErrorLocal(null)
    try {
      const base = brief || await (await fetch(`${API_BASE_URL}/api/brief/example`)).json()
      const resp = await fetch(`${API_BASE_URL}/api/concepts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brief: base, count: 4 }),
      })
      if (!resp.ok) throw new Error(`concepts failed: ${resp.status}`)
      setConcepts((await resp.json()).concepts)
    } catch (e) {
      setErrorLocal(e.message)
    } finally {
      setBusy(false)
    }
  }

  async function loadConcept(c) {
    setLoading()
    setBrief(c.brief)
    try {
      const resp = await fetch(`${API_BASE_URL}/api/engineering/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(c.brief),
      })
      if (!resp.ok) throw new Error(`engineering failed: ${resp.status}`)
      setEngineering(await resp.json())
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="panel">
      <h2>Concept alternatives</h2>
      <button className="btn primary" onClick={generate} disabled={busy}>
        {busy ? 'Generating…' : 'Generate 4 concepts'}
      </button>
      {error && <p className="error">{error}</p>}
      {concepts && concepts.map((c) => (
        <div key={c.theme} style={styles.card}>
          <div style={styles.cardHead}>
            <strong>{c.theme}</strong>
            <span style={{ color: c.headline.gates_pass ? '#7bd88a' : '#ff6b6b' }}>
              {c.headline.gates_pass ? 'gates PASS' : 'gates FAIL'}
            </span>
          </div>
          <div style={styles.meta}>
            {c.brief.sculpture.family} · {c.brief.sculpture.material} ·{' '}
            {c.headline.mass_kg.toFixed(0)} kg · ${c.headline.total_usd.toLocaleString()}
          </div>
          <button className="btn" onClick={() => loadConcept(c)}>
            Load this concept
          </button>
        </div>
      ))}
      <p className="hint">Each concept is fully engineered — not a random image.</p>
    </div>
  )
}

const styles = {
  card: {
    border: '1px solid var(--border)', borderRadius: '4px',
    padding: '10px', display: 'flex', flexDirection: 'column', gap: '6px',
  },
  cardHead: { display: 'flex', justifyContent: 'space-between' },
  meta: { color: 'var(--text-dim)', fontSize: '12px' },
}
