import { create } from 'zustand'
import { API_BASE_URL } from '../config'
import { FAMILIES } from '../families'

// The design brief is the single source of truth (PLAN.md §4);
// `engineering` holds the last /api/engineering/run result derived from it.
//
// Live studio (Forma/TestFit lesson): every brief edit schedules a debounced
// engineering run; the previous in-flight request is aborted and stale
// responses are dropped, so the UI always converges on the latest edit.
const RUN_DEBOUNCE_MS = 350
let runTimer = null
let runAbort = null
let runSeq = 0

// Immutable deep set by dotted path ("water.features.1.count").
function setPath(obj, path, value) {
  const keys = path.split('.')
  const walk = (node, i) => {
    if (i === keys.length) return value
    const k = keys[i]
    if (Array.isArray(node)) {
      const copy = node.slice()
      copy[Number(k)] = walk(node[Number(k)], i + 1)
      return copy
    }
    return { ...(node || {}), [k]: walk(node ? node[k] : undefined, i + 1) }
  }
  return walk(obj, 0)
}

function changedGateIds(prev, next) {
  if (!prev?.gates?.gates || !next?.gates?.gates) return []
  const before = Object.fromEntries(prev.gates.gates.map((g) => [g.id, g.status]))
  return next.gates.gates.filter((g) => before[g.id] !== g.status).map((g) => g.id)
}

const useBriefStore = create((set, get) => ({
  brief: null,
  engineering: null,
  prevEngineering: null, // previous run — drives the KPI deltas
  status: 'idle', // idle | loading | error   (explicit Generate only)
  stale: false,   // true while a live re-run is pending/in flight
  error: null,
  family: 'open_ring',
  show: [],          // light show segments (scope §14); empty = backend default
  backendUp: null,   // null = unknown, true/false after health ping
  dockFocus: null,   // {side, tab} — gate bar click-through
  catalog: null,     // /api/geometry/families → { family: [param meta] }
  lastRunMs: null,
  runId: 0,
  changedGates: [],  // gate ids whose status changed on the last run

  setDockFocus: (dockFocus) => set({ dockFocus }),
  setFamily: (family) => set({ family }),
  setBrief: (brief) => set({ brief }),
  setShow: (show) => set({ show }),
  setBackendUp: (backendUp) => set({ backendUp }),
  setLoading: () => set({ status: 'loading', error: null }),
  setError: (error) => set({ status: 'error', error, stale: false }),
  setEngineering: (engineering) => set((s) => ({
    prevEngineering: s.engineering,
    engineering,
    status: 'idle',
    stale: false,
    runId: s.runId + 1,
    changedGates: changedGateIds(s.engineering, engineering),
  })),

  loadCatalog: async () => {
    if (get().catalog) return get().catalog
    try {
      const r = await fetch(`${API_BASE_URL}/api/geometry/families`)
      if (!r.ok) return null
      const catalog = Object.fromEntries(
        (await r.json()).families.map((f) => [f.family, f.params]))
      set({ catalog })
      return catalog
    } catch {
      return null
    }
  },

  // House defaults (portfolio-tuned, families.js) overlay the generator
  // signature defaults from the catalog.
  familyDefaults: (family) => {
    const sig = Object.fromEntries(
      (get().catalog?.[family] || []).map((p) => [p.name, p.default]))
    return { ...sig, ...(FAMILIES[family]?.defaults || {}) }
  },

  // Edit one brief field and schedule a live engineering run.
  updateBrief: (path, value) => {
    const { brief } = get()
    if (!brief) return
    set({ brief: setPath(brief, path, value), stale: true })
    get().scheduleRun()
  },

  // Changing family swaps the parameter block for that family's defaults.
  changeFamily: (family) => {
    const { brief } = get()
    if (!brief) return
    const next = {
      ...brief,
      sculpture: { ...brief.sculpture, family, parameters: get().familyDefaults(family) },
    }
    set({ brief: next, family, stale: true })
    get().scheduleRun()
  },

  scheduleRun: () => {
    clearTimeout(runTimer)
    runTimer = setTimeout(() => get()._runEngineering(get().brief, { live: true }),
                          RUN_DEBOUNCE_MS)
  },

  // Shared: run the deterministic engineering loop on a brief.
  _runEngineering: async (brief, { live = false } = {}) => {
    if (!brief) return
    const { show } = get()
    const finalBrief = show.length
      ? { ...brief, lighting: { ...(brief.lighting || {}), show } }
      : brief
    runAbort?.abort()
    const controller = new AbortController()
    runAbort = controller
    const seq = ++runSeq
    const t0 = performance.now()
    if (live) set({ stale: true })
    try {
      const engResp = await fetch(`${API_BASE_URL}/api/engineering/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(finalBrief),
        signal: controller.signal,
      })
      if (seq !== runSeq) return // a newer edit superseded this run
      if (!engResp.ok) {
        const detail = await engResp.text()
        throw new Error(`engineering run failed (${engResp.status}): ${detail.slice(0, 200)}`)
      }
      const engineering = await engResp.json()
      if (seq !== runSeq) return
      get().setEngineering(engineering)
      set({ lastRunMs: Math.round(performance.now() - t0), error: null })
    } catch (e) {
      if (e.name === 'AbortError') return
      if (seq !== runSeq) return
      get().setError(e.message)
    }
  },

  // Phase 2: natural-language prompt -> AI design brief -> engineering loop.
  runPromptGeneration: async (prompt) => {
    set({ status: 'loading', error: null })
    try {
      const aiResp = await fetch(`${API_BASE_URL}/api/ai/interpret`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      })
      if (!aiResp.ok) {
        const detail = await aiResp.text()
        throw new Error(`AI interpret failed (${aiResp.status}): ${detail.slice(0, 200)}`)
      }
      const { brief } = await aiResp.json()
      set({ brief, family: brief.sculpture?.family || get().family })
      await get()._runEngineering(brief)
    } catch (e) {
      set({ status: 'error', error: e.message })
    }
  },

  // Phase 1: no AI yet — build a brief from the example + selected family,
  // then run the full deterministic loop (geometry → engineering → cost).
  runGeneration: async () => {
    const { family } = get()
    set({ status: 'loading', error: null })
    try {
      await get().loadCatalog()
      const briefResp = await fetch(`${API_BASE_URL}/api/brief/example`)
      if (!briefResp.ok) throw new Error(`backend returned ${briefResp.status}`)
      const brief = await briefResp.json()
      const runBrief = {
        ...brief,
        sculpture: { ...brief.sculpture, family,
                     parameters: get().familyDefaults(family) },
      }
      set({ brief: runBrief })
      await get()._runEngineering(runBrief)
    } catch (e) {
      set({ status: 'error',
            error: `Could not reach the backend at ${API_BASE_URL}: ${e.message}` })
    }
  },
}))

export default useBriefStore
