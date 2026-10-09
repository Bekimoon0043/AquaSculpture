import { useEffect, useRef, useState } from 'react'
import useBriefStore from '../store/briefStore'

// Conversational prompt console (Zookeeper/Meshy/Zoo lessons): a chat log
// instead of a one-shot box; each assistant turn echoes what was understood
// and lists the exact brief fields it changed; portfolio chips coach prompts.

// The nine reference works (PLAN.md §2.1) — the archetype acceptance test.
export const PORTFOLIO_PROMPTS = [
  { id: 'P1', label: 'Arc-fin array + map', text: 'A radial array of 8 brushed stainless curved tapered fins, 3 m tall, around a backlit perforated Africa-map relief panel, with rain curtains between the arcs and an RGB foam-jet field, in a 10 m circular granite plaza basin, budget $400k' },
  { id: 'P2', label: 'Twisted white seed', text: 'A 4 m twisted white GRC ring like a seed, matte painted, on a rectangular 8 x 5 m black granite reflecting pool with 12 bubbler jets, residential plaza' },
  { id: 'P3', label: 'Bronze flame-wing', text: 'A 3 m patinated cast bronze flame with 4 flowing ribbed lobes in a 5 m circular marble basin with still water, interior atrium' },
  { id: 'P4', label: 'Tall ribbon knot', text: 'A 5 m dark-patina bronze ribbon knot, vertical figure-eight, in a 6 m circular marble basin, atrium with oculus' },
  { id: 'P5', label: 'Mirror fluid form', text: 'A 3.5 m mirror-polished stainless flowing flame form with water sheeting off its body and mushroom bubblers, rectangular 6 x 4 m stainless basin, hotel lobby, budget $300k' },
  { id: 'P6', label: 'Crescent + bird', text: 'A 1.9 m mirror-polished stainless open crescent ring with a suspended bird silhouette inside, dry, base plate mount, factory courtyard' },
  { id: 'P7', label: 'Infinity flame', text: 'A 6 m mirror-polished stainless infinity flame, vertical double loop, dry on a garden lawn, moderate wind' },
  { id: 'P8', label: 'Stacked loops totem', text: 'A 4 m mirror-polished stainless totem of stacked open rings and elliptical disks, dry, garden courtyard' },
  { id: 'P9', label: 'Stacked C-rings', text: 'A 4 m stacked C-rings fountain in brushed and textured stainless, rings increasing in diameter with a water curtain between rings and perimeter mist, 6 m circular black granite basin, outdoor park, budget $250k' },
]

const fmt = (v) => v == null ? '—' : typeof v === 'object' ? JSON.stringify(v) : String(v)

function AssistantCard({ entry }) {
  if (entry.error) return <div className="chat-card error-card">{entry.error}</div>
  return (
    <div className="chat-card">
      <div className="chat-echo">
        <span className="chat-tag">I read</span>
        {entry.summary}
      </div>
      {entry.changes?.length > 0 && (
        <ul className="chat-changes">
          {entry.changes.map((c) => (
            <li key={c.path}>
              <code>{c.path}</code>
              <span className="before">{fmt(c.before)}</span>
              <span className="arrow">→</span>
              <span className="after">{fmt(c.after)}</span>
            </li>
          ))}
        </ul>
      )}
      {entry.changes && entry.changes.length === 0 && (
        <p className="hint">No brief fields changed.</p>
      )}
      {entry.provider && <span className="chat-provider">{entry.provider}</span>}
    </div>
  )
}

export default function PromptConsole() {
  const [text, setText] = useState('')
  const { chat, brief, status, error, sendMessage, runGeneration, clearChat } = useBriefStore()
  const logRef = useRef(null)
  const busy = status === 'loading'

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight })
  }, [chat.length, busy])

  function send() {
    const t = text.trim()
    if (busy) return
    if (!t) { runGeneration(); return }   // empty = toolbar family demo
    setText('')
    sendMessage(t)
  }

  function onKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  return (
    <div className="panel chat">
      <div className="panel-head">
        <h2>{brief ? 'Refine' : 'Prompt'}</h2>
        {chat.length > 0 && <button className="btn mini" onClick={clearChat}>Clear</button>}
      </div>

      <div className="chat-log" ref={logRef}>
        {chat.length === 0 && (
          <p className="hint">
            Describe the piece — dimensions, material and finish, water effects,
            site and budget. Then keep talking: "make it bronze", "20% taller",
            "add 12 bubblers". Every reply shows what was understood and which
            brief fields changed; engineering re-runs each time.
          </p>
        )}
        {chat.map((m, i) => m.role === 'user'
          ? <div key={i} className="chat-user">{m.text}</div>
          : <AssistantCard key={i} entry={m} />)}
        {busy && <div className="chat-card"><span className="hint">thinking…</span></div>}
      </div>

      {chat.length === 0 && (
        <div className="chips" title="Reference portfolio (PLAN §2) — one click loads the prompt">
          {PORTFOLIO_PROMPTS.map((p) => (
            <button key={p.id} className="chip" onClick={() => setText(p.text)}
                    title={p.text}>
              {p.id} {p.label}
            </button>
          ))}
        </div>
      )}

      <textarea
        placeholder={brief
          ? 'Change something: "make it bronze with a patina", "6 m tall", "indoor lobby, no wind"…'
          : 'e.g. "A 4 m mirror-polished stainless open-ring sculpture with water sheeting down its face, on a 6 m circular black granite basin with 12 bubbler jets, for a hotel atrium, budget $250k"'}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={onKey}
        rows={3}
      />
      <button className="btn primary" onClick={send} disabled={busy}>
        {busy ? 'Working…' : brief ? (text.trim() ? 'Refine' : 'Regenerate demo') : (text.trim() ? 'Generate' : 'Generate demo')}
      </button>
      {error && !chat.some((m) => m.error === error) && <p className="error">{error}</p>}
      <p className="hint">Enter sends · Shift+Enter for a new line · empty prompt = demo of the toolbar family</p>
    </div>
  )
}
