import useBriefStore from '../store/briefStore'

export default function BriefEditor() {
  const brief = useBriefStore((s) => s.brief)

  return (
    <div style={styles.panel}>
      <h2 style={styles.heading}>Design Brief</h2>
      <pre style={styles.json}>
        {brief ? JSON.stringify(brief, null, 2) : 'No brief yet — press Generate.'}
      </pre>
    </div>
  )
}

const styles = {
  panel: {
    padding: '12px', display: 'flex', flexDirection: 'column',
    height: '100%', boxSizing: 'border-box', overflow: 'hidden',
  },
  heading: { margin: 0, fontSize: '14px', color: '#ccc', textTransform: 'uppercase' },
  json: {
    flex: 1, overflow: 'auto', background: '#1b1e24', color: '#a8d8a8',
    border: '1px solid #333', borderRadius: '4px', padding: '8px',
    fontSize: '12px', margin: '8px 0 0',
  },
}
