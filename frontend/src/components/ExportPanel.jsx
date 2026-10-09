import { useState } from 'react'
import { API_BASE_URL } from '../config'
import useBriefStore from '../store/briefStore'
import { viewerRef } from '../viewerRef'

function download(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default function ExportPanel() {
  const brief = useBriefStore((s) => s.brief)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const project = (brief?.project?.name || 'aquasculptor').replace(/\s+/g, '_')

  async function post(endpoint, filename) {
    setBusy(true)
    setError(null)
    try {
      const resp = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(brief),
      })
      if (!resp.ok) throw new Error(`${endpoint} failed: ${resp.status}`)
      download(await resp.blob(), filename)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  function snapshot() {
    const canvas = viewerRef.canvas
    if (!canvas) return setError('viewport not ready')
    canvas.toBlob((blob) => download(blob, `${project}_render.png`), 'image/png')
  }

  return (
    <div className="panel">
      <h2>Export</h2>
      <button className="btn primary" disabled={!brief || busy}
              onClick={() => post('/api/deliverables/package', `${project}_package.zip`)}>
        {busy ? 'Packaging…' : 'Engineering package (ZIP)'}
      </button>
      <p className="hint">
        brief · STL · GLB · STEP · IGES · panels.dxf · GA + foundation drawings ·
        BOM/BOQ · PDF report + quotation · SHA-256 manifest
      </p>
      <button className="btn" disabled={!brief || busy}
              onClick={() => post('/api/integration/aquaflow', `${project}.luxexchange.json`)}>
        AquaFlow exchange (LUXEXCHANGE)
      </button>
      <p className="hint">Fixtures, DMX patch, devices, show program for AquaFlow.</p>
      <button className="btn" onClick={snapshot}>
        Viewport snapshot (PNG)
      </button>
      <p className="hint">Client-presentation render of the current view.</p>
      {error && <p className="error">{error}</p>}
    </div>
  )
}
