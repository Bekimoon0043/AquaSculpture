import useBriefStore from '../store/briefStore'

// Pipeline gate bar (house style): G0..G10 as steps with connector lines.
// Glyph ring color = gate status; tooltip carries the gate note.
export default function PipelineBar() {
  const gates = useBriefStore((s) => s.engineering?.gates)

  return (
    <div style={styles.bar}>
      {(gates?.gates || PLACEHOLDER).map((g, i) => (
        <div key={g.id} style={styles.item} title={g.note || g.label}>
          {i > 0 && <span style={styles.link} />}
          <span style={{ ...styles.glyph, ...glyphStyle(g.status) }}>
            {g.id}
          </span>
          <span style={styles.text}>
            <span style={styles.label}>{g.label}</span>
            <span style={styles.detail}>{g.status.replace('_', ' ')}</span>
          </span>
        </div>
      ))}
    </div>
  )
}

const PLACEHOLDER = [
  ['G0', 'Brief'], ['G1', 'Concept'], ['G2', 'Geometry'], ['G3', 'Material'],
  ['G4', 'Structural'], ['G5', 'Hydraulic'], ['G6', 'Lighting'],
  ['G7', 'Fabrication'], ['G8', 'Maintainability'], ['G9', 'Cost'],
  ['G10', 'Package'],
].map(([id, label]) => ({ id, label, status: 'not_evaluated', note: '' }))

function glyphStyle(status) {
  switch (status) {
    case 'pass': return { color: 'var(--ok)', borderColor: 'var(--ok)' }
    case 'warning': return { color: 'var(--warn)', borderColor: 'var(--warn)' }
    case 'fail': return { color: 'var(--danger)', borderColor: 'var(--danger)' }
    default: return { color: 'var(--text-faint)', borderColor: 'var(--line-strong, #3d4650)' }
  }
}

const styles = {
  bar: {
    display: 'flex', alignItems: 'center', gap: 0, overflowX: 'auto',
    background: 'var(--bg-chrome)', borderBottom: '1px solid var(--border)',
    padding: '4px 10px', flexShrink: 0, scrollbarWidth: 'none',
  },
  item: { display: 'flex', alignItems: 'center', cursor: 'default', flexShrink: 0 },
  link: { width: '14px', height: '1px', background: 'var(--border)', flexShrink: 0 },
  glyph: {
    border: '1px solid', borderRadius: '50%', width: '24px', height: '24px',
    display: 'grid', placeItems: 'center', fontSize: '9px', fontWeight: 700,
    flexShrink: 0,
  },
  text: { display: 'flex', flexDirection: 'column', lineHeight: 1.15, padding: '0 6px' },
  label: { fontSize: '11px', fontWeight: 600, whiteSpace: 'nowrap' },
  detail: { fontSize: '9px', color: 'var(--text-faint)', whiteSpace: 'nowrap' },
}
