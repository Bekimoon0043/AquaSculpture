import { useState } from 'react'
import useBriefStore from '../store/briefStore'

export default function PromptConsole() {
  const [prompt, setPrompt] = useState('')
  const { status, error, runGeneration, runPromptGeneration } = useBriefStore()

  function handleGenerate() {
    // With prompt text: AI interpreter (Phase 2). Empty: toolbar family demo.
    if (prompt.trim()) runPromptGeneration(prompt.trim())
    else runGeneration()
  }

  return (
    <div className="panel">
      <h2>Prompt</h2>
      <textarea
        placeholder='e.g. "A 4 m mirror-polished stainless open-ring sculpture with water sheeting down its face, on a 6 m circular black granite basin with 12 bubbler jets, for a hotel atrium, budget $250k"'
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
      />
      <button
        className="btn primary"
        onClick={handleGenerate}
        disabled={status === 'loading'}
      >
        {status === 'loading' ? 'Generating…' : 'Generate'}
      </button>
      {error && <p className="error">{error}</p>}
      <p className="hint">
        Type a description and the AI turns it into an engineered design.
        Empty prompt = demo of the family selected in the toolbar.
      </p>
    </div>
  )
}
