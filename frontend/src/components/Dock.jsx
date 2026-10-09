import { useEffect, useState } from 'react'

// Collapsible tabbed dock (Blender/C4D idiom): tabs on top, one panel
// visible at a time, whole dock collapses to a strip to free the viewport.
export default function Dock({ side, tabs, focus = 0 }) {
  const [active, setActive] = useState(0)
  const [collapsed, setCollapsed] = useState(false)

  // Gate-bar click-through: external focus request opens this tab.
  useEffect(() => {
    if (focus != null) {
      setActive(focus)
      setCollapsed(false)
    }
  }, [focus])

  if (collapsed) {
    return (
      <div className={`dock ${side} collapsed`}>
        <button
          className="dock-collapse"
          title="Expand panel"
          onClick={() => setCollapsed(false)}
        >
          {side === 'left' ? '»' : '«'}
        </button>
      </div>
    )
  }

  return (
    <div className={`dock ${side}`}>
      <div className="dock-tabs">
        {tabs.map((t, i) => (
          <button
            key={t.label}
            className={`dock-tab ${i === active ? 'active' : ''}`}
            onClick={() => setActive(i)}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="dock-body">{tabs[active].node}</div>
      <button
        className="dock-collapse"
        title="Collapse panel"
        onClick={() => setCollapsed(true)}
      >
        {side === 'left' ? '« Collapse' : 'Collapse »'}
      </button>
    </div>
  )
}
