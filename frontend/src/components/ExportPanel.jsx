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
  const engineering = useBriefStore((s) => s.engineering)
  const approve = useBriefStore((s) => s.approve)
  const approver = useBriefStore((s) => s.approver)
  const setApprover = useBriefStore((s) => s.setApprover)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const project = (brief?.project?.name || 'aquasculptor').replace(/\s+/g, '_')

  // G10 (Onshape release lesson): sign-off is human, but only offered when
  // every automatic gate is pass/warning — and it is void on any failure.
  const gates = engineering?.gates?.gates || []
  const blocking = gates.filter((g) => g.id !== 'G10' && g.status === 'fail')
  const open = gates.filter((g) => g.id !== 'G10' && g.status === 'not_evaluated')
  const canApprove = engineering && blocking.length === 0 && open.length === 0
  const g10 = brief?.approvals?.G10

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

      <h3 className="form-section">G10 · Production package approval</h3>
      {g10 ? (
        <div className={`approval ${engineering?.gates?.production_ready ? 'ok' : 'bad'}`}>
          {engineering?.gates?.production_ready ? 'PRODUCTION READY — ' : 'APPROVAL VOID (gate failure) — '}
          signed by <strong>{g10.by}</strong> on {g10.at.slice(0, 10)}{g10.note ? ` — ${g10.note}` : ''}
          <button className="btn mini" onClick={() => approve('G10', null)}>Revoke</button>
        </div>
      ) : (
        <>
          <div className="approval">
            <input type="text" placeholder="approver" value={approver} onChange={(e) => setApprover(e.target.value)} />
            <button className="btn" disabled={!canApprove || !approver.trim()}
                    onClick={() => approve('G10', { by: approver.trim(), note: 'production package approved' })}>
              Approve package
            </button>
          </div>
          {engineering && !canApprove && (
            <p className="hint">
              {blocking.length > 0 && `Blocked by failing gate${blocking.length > 1 ? 's' : ''}: ${blocking.map((g) => g.id).join(', ')}. `}
              {open.length > 0 && `Open: ${open.map((g) => `${g.id} ${g.label}`).join(', ')}.`}
            </p>
          )}
        </>
      )}

      <h3 className="form-section">Deliverables</h3>
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
