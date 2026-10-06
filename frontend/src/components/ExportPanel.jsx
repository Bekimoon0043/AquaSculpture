import { useState } from 'react'
import { API_BASE_URL } from '../config'
import useBriefStore from '../store/briefStore'

export default function ExportPanel() {
  const brief = useBriefStore((s) => s.brief)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function handleDownload() {
    setBusy(true)
    setError(null)
    try {
      const resp = await fetch(`${API_BASE_URL}/api/deliverables/package`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(brief),
      })
      if (!resp.ok) throw new Error(`package failed: ${resp.status}`)
      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${(brief?.project?.name || 'sculptflow').replace(/\s+/g, '_')}_package.zip`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={styles.panel}>
      <h2 style={styles.heading}>Export</h2>
      <button style={styles.button} onClick={handleDownload} disabled={!brief || busy}>
        {busy ? 'Packaging…' : 'Download package (ZIP)'}
      </button>
      {error && <p style={styles.error}>{error}</p>}
      <p style={styles.hint}>STL + GLB + PDF report + XLSX BOM + brief + SHA-256 manifest.</p>
    </div>
  )
}

const styles = {
  panel: { padding: '12px' },
  heading: { margin: '0 0 8px', fontSize: '14px', color: '#ccc', textTransform: 'uppercase' },
  button: {
    background: '#2e9e5b', color: '#fff', border: 'none', borderRadius: '4px',
    padding: '8px 16px', cursor: 'pointer', fontWeight: 600,
  },
  error: { color: '#ff6b6b', fontSize: '13px' },
  hint: { color: '#666', fontSize: '12px' },
}
