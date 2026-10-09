import { useEffect, useState } from 'react'
import useBriefStore from './store/briefStore'
import Toolbar from './components/Toolbar'
import PipelineBar from './components/PipelineBar'
import Dock from './components/Dock'
import StatusBar from './components/StatusBar'
import PromptConsole from './components/PromptConsole'
import Viewer3D from './components/Viewer3D'
import BriefEditor from './components/BriefEditor'
import EngineeringPanel from './components/EngineeringPanel'
import CostPanel from './components/CostPanel'
import TimelinePanel from './components/TimelinePanel'
import CopilotPanel from './components/CopilotPanel'
import ConceptsPanel from './components/ConceptsPanel'
import ExportPanel from './components/ExportPanel'

export default function App() {
  const dockFocus = useBriefStore((s) => s.dockFocus)
  const [leftFocus, setLeftFocus] = useState(null)
  const [rightFocus, setRightFocus] = useState(null)

  useEffect(() => {
    if (!dockFocus) return
    if (dockFocus.side === 'left') setLeftFocus(dockFocus.tab)
    else setRightFocus(dockFocus.tab)
  }, [dockFocus])

  return (
    <div className="app-shell">
      <Toolbar />
      <PipelineBar />
      <div className="app-main">
        <Dock
          side="left"
          focus={leftFocus}
          tabs={[
            { label: 'Prompt', node: <PromptConsole /> },
            { label: 'Brief', node: <BriefEditor /> },
            { label: 'Concepts', node: <ConceptsPanel /> },
            { label: 'Copilot', node: <CopilotPanel /> },
          ]}
        />
        <div className="viewport">
          <Viewer3D />
        </div>
        <Dock
          side="right"
          focus={rightFocus}
          tabs={[
            { label: 'Engineering', node: <EngineeringPanel /> },
            { label: 'Cost', node: <CostPanel /> },
            { label: 'Show', node: <TimelinePanel /> },
            { label: 'Export', node: <ExportPanel /> },
          ]}
        />
      </div>
      <StatusBar />
    </div>
  )
}
