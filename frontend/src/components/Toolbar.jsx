import useBriefStore from '../store/briefStore'
import { FAMILIES } from '../families'

export default function Toolbar() {
  const { family, setFamily, status, runGeneration } = useBriefStore()

  return (
    <div className="toolbar">
      <span className="brand">
        <img src="/logo.svg" alt="AquaSculptor"
             style={{ height: '26px', width: '26px', borderRadius: '6px' }} />
        AquaSculptor
      </span>
      <span className="sep" />
      <label htmlFor="family-select" style={{ color: 'var(--text-dim)' }}>Family</label>
      <select
        id="family-select"
        value={family}
        onChange={(e) => setFamily(e.target.value)}
      >
        {Object.entries(FAMILIES).map(([key, f]) => (
          <option key={key} value={key}>{f.label}</option>
        ))}
      </select>
      <button
        className="btn primary"
        onClick={runGeneration}
        disabled={status === 'loading'}
      >
        {status === 'loading' ? 'Generating…' : 'Generate'}
      </button>
    </div>
  )
}
