import Toolbar from './components/Toolbar'
import Dock from './components/Dock'
import StatusBar from './components/StatusBar'
import PromptConsole from './components/PromptConsole'
import Viewer3D from './components/Viewer3D'
import BriefEditor from './components/BriefEditor'
import EngineeringPanel from './components/EngineeringPanel'
import CostPanel from './components/CostPanel'
import TimelinePanel from './components/TimelinePanel'
import ExportPanel from './components/ExportPanel'

export default function App() {
  return (
    <div className="app-shell">
      <Toolbar />
      <div className="app-main">
        <Dock
          side="left"
          tabs={[
            { label: 'Prompt', node: <PromptConsole /> },
            { label: 'Brief', node: <BriefEditor /> },
          ]}
        />
        <div className="viewport">
          <Viewer3D />
        </div>
        <Dock
          side="right"
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
