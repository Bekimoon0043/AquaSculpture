import { useEffect, useState } from 'react'
import useBriefStore from '../store/briefStore'
import { FAMILIES } from '../families'

export default function Toolbar() {
  const { family, setFamily, changeFamily, brief, status, runGeneration,
          projects, listProjects, saveProject, loadProject } = useBriefStore()
  const [name, setName] = useState('')
  const [open, setOpen] = useState('')

  useEffect(() => { listProjects() }, [listProjects])
  useEffect(() => { if (brief?.project?.name) setName(brief.project.name) }, [brief?.project?.name])

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
        onChange={(e) => (brief ? changeFamily : setFamily)(e.target.value)}
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

      <span className="sep" />
      <label style={{ color: 'var(--text-dim)' }}>Project</label>
      <input className="project-name" type="text" placeholder="name" value={name}
             onChange={(e) => setName(e.target.value)} />
      <button className="btn" disabled={!brief || !name.trim()} title="Save brief + show + approvals"
              onClick={() => saveProject(name.trim())}>
        Save
      </button>
      <select value={open} title="Open a saved project"
              onChange={(e) => { setOpen(''); if (e.target.value) loadProject(e.target.value) }}>
        <option value="">Open…</option>
        {projects.map((p) => <option key={p} value={p}>{p}</option>)}
      </select>
    </div>
  )
}
