import { create } from 'zustand'
import { API_BASE_URL } from '../config'
import { FAMILIES } from '../families'

// The design brief is the single source of truth (PLAN.md §4);
// `engineering` holds the last /api/engineering/run result derived from it.
const useBriefStore = create((set, get) => ({
  brief: null,
  engineering: null,
  status: 'idle', // idle | loading | error
  error: null,
  family: 'open_ring',
  show: [],          // light show segments (scope §14); empty = backend default
  backendUp: null,   // null = unknown, true/false after health ping
  dockFocus: null,   // {side, index} — gate bar click-through
  setDockFocus: (dockFocus) => set({ dockFocus }),
  setFamily: (family) => set({ family }),
  setBrief: (brief) => set({ brief }),
  setShow: (show) => set({ show }),
  setBackendUp: (backendUp) => set({ backendUp }),

  // Shared: run the deterministic engineering loop on a brief.
  _runEngineering: async (brief) => {
    const { show } = get()
    const finalBrief = show.length
      ? { ...brief, lighting: { ...(brief.lighting || {}), show } }
      : brief
    const engResp = await fetch(`${API_BASE_URL}/api/engineering/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(finalBrief),
    })
    if (!engResp.ok) {
      const detail = await engResp.text()
      throw new Error(`engineering run failed (${engResp.status}): ${detail.slice(0, 200)}`)
    }
    set({ engineering: await engResp.json(), status: 'idle' })
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
      set({ brief })
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
      const briefResp = await fetch(`${API_BASE_URL}/api/brief/example`)
      if (!briefResp.ok) throw new Error(`backend returned ${briefResp.status}`)
      const brief = await briefResp.json()
      const runBrief = {
        ...brief,
        sculpture: { ...brief.sculpture, family,
                     parameters: FAMILIES[family].defaults },
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
