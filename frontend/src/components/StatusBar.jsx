import { useEffect } from 'react'
import { API_BASE_URL } from '../config'
import useBriefStore from '../store/briefStore'

export default function StatusBar() {
  const { engineering, status, stale, lastRunMs, backendUp, setBackendUp } = useBriefStore()

  useEffect(() => {
    let alive = true
    async function ping() {
      try {
        const r = await fetch(`${API_BASE_URL}/api/health`)
        if (alive) setBackendUp(r.ok)
      } catch {
        if (alive) setBackendUp(false)
      }
    }
    ping()
    const t = setInterval(ping, 10000)
    return () => { alive = false; clearInterval(t) }
  }, [setBackendUp])

  const mesh = engineering?.sculpture?.mesh
  const verts = mesh ? mesh.vertices.length : 0
  const faces = mesh ? mesh.faces.length : 0

  return (
    <div className="statusbar">
      <span>
        <span className={`dot ${backendUp ? 'up' : 'down'}`} />
        Backend {backendUp === null ? '…' : backendUp ? 'connected' : 'offline'}
      </span>
      <span>{verts.toLocaleString()} verts / {faces.toLocaleString()} faces</span>
      <span className="spacer" />
      {lastRunMs != null && <span title="Last full engineering run">engineering {(lastRunMs / 1000).toFixed(1)} s</span>}
      <span>{status === 'loading' ? 'Running engineering…' : stale ? 'Updating…' : status === 'error' ? 'Error' : 'Ready'}</span>
    </div>
  )
}
