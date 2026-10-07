import useBriefStore from '../store/briefStore'

const EFFECTS = ['fade', 'pulse', 'chase', 'gradient', 'wave', 'sparkle', 'strobe', 'transition']
const ZONES = ['all', 'sculpture', 'basin']

// Dynamic light show editor (scope §14): segments -> brief.lighting.show ->
// compiled per-fixture program handed to AquaFlow.
export default function TimelinePanel() {
  const { show, setShow } = useBriefStore()

  function update(i, patch) {
    setShow(show.map((s, j) => (j === i ? { ...s, ...patch } : s)))
  }
  function remove(i) {
    setShow(show.filter((_, j) => j !== i))
  }
  function add() {
    const start = show.length
      ? Math.max(...show.map((s) => s.start_s + s.duration_s))
      : 0
    setShow([...show, { start_s: start, duration_s: 5, effect: 'fade',
                        color: '#ffb85c', color_to: '#3c82ff', zones: ['all'] }])
  }

  const total = show.length
    ? Math.max(...show.map((s) => s.start_s + s.duration_s)) : 0

  return (
    <div className="panel">
      <h2>Light show timeline</h2>
      {show.map((s, i) => (
        <div key={i} style={styles.seg}>
          <div style={styles.row}>
            <strong style={{ color: 'var(--accent)' }}>#{i + 1}</strong>
            <select value={s.effect} onChange={(e) => update(i, { effect: e.target.value })}>
              {EFFECTS.map((e) => <option key={e} value={e}>{e}</option>)}
            </select>
            <select value={s.zones[0]}
                    onChange={(e) => update(i, { zones: [e.target.value] })}>
              {ZONES.map((z) => <option key={z} value={z}>{z}</option>)}
            </select>
            <button className="btn" onClick={() => remove(i)}>✕</button>
          </div>
          <div style={styles.row}>
            <input type="color" value={s.color}
                   onChange={(e) => update(i, { color: e.target.value })} />
            <input type="color" value={s.color_to || s.color}
                   onChange={(e) => update(i, { color_to: e.target.value })} />
            <label style={{ color: 'var(--text-dim)' }}>
              start
              <input type="number" min="0" step="0.5" value={s.start_s}
                     style={styles.num}
                     onChange={(e) => update(i, { start_s: +e.target.value })} />
            </label>
            <label style={{ color: 'var(--text-dim)' }}>
              dur
              <input type="number" min="0.5" step="0.5" value={s.duration_s}
                     style={styles.num}
                     onChange={(e) => update(i, { duration_s: +e.target.value })} />
            </label>
          </div>
        </div>
      ))}
      <button className="btn" onClick={add}>+ Add segment</button>
      <p className="hint">
        {show.length} segment(s), {total.toFixed(0)} s total. Compiled into the
        brief on Generate and shipped to AquaFlow via LUXEXCHANGE.
      </p>
    </div>
  )
}

const styles = {
  seg: {
    border: '1px solid var(--border)', borderRadius: '4px',
    padding: '8px', display: 'flex', flexDirection: 'column', gap: '6px',
  },
  row: { display: 'flex', gap: '6px', alignItems: 'center' },
  num: { width: '54px', background: 'var(--bg-panel)', color: 'var(--text)',
         border: '1px solid var(--border)', borderRadius: '3px',
         padding: '2px 4px', marginLeft: '4px' },
}
