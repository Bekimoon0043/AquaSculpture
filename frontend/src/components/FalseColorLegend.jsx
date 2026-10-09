// Shared false-colour system (DIALux lesson): one ramp for every discipline
// overlay (lux on the shell, utilisation on the skeleton), a legend with the
// value range, an optional threshold line (code minimum / unity) and a
// soft-vs-hard-step toggle — "hard steps are easier to read, soft is prettier".

export const STEPS = 7

// t in [0,1] -> [r,g,b] in [0,1]; blue -> cyan -> green -> yellow -> red.
export function ramp(t, steps = 0) {
  let x = Math.min(Math.max(t, 0), 1)
  if (steps > 0) x = Math.round(x * (steps - 1)) / (steps - 1)
  const stops = [
    [0.00, [0.13, 0.22, 0.75]],
    [0.25, [0.10, 0.65, 0.90]],
    [0.50, [0.20, 0.78, 0.35]],
    [0.75, [0.95, 0.85, 0.20]],
    [1.00, [0.85, 0.15, 0.12]],
  ]
  for (let i = 1; i < stops.length; i++) {
    const [t0, c0] = stops[i - 1], [t1, c1] = stops[i]
    if (x <= t1) {
      const u = (x - t0) / (t1 - t0)
      return [0, 1, 2].map((k) => c0[k] + (c1[k] - c0[k]) * u)
    }
  }
  return stops[stops.length - 1][1]
}

const css = (c) => `rgb(${c.map((v) => Math.round(v * 255)).join(',')})`

export function gradientCSS(steps = 0) {
  const n = steps > 0 ? steps : 24
  const parts = []
  for (let i = 0; i < n; i++) {
    const a = i / n, b = (i + 1) / n
    const c = css(ramp(steps > 0 ? a : (a + b) / 2, steps))
    parts.push(steps > 0 ? `${c} ${a * 100}% ${b * 100}%` : `${c} ${((a + b) / 2) * 100}%`)
  }
  return `linear-gradient(to right, ${parts.join(', ')})`
}

export default function FalseColorLegend({ label, unit, min, max, threshold,
                                           thresholdLabel, steps, onToggleSteps,
                                           children }) {
  const span = max - min || 1
  const tPos = threshold != null ? ((threshold - min) / span) * 100 : null
  const fmt = (v) => Math.abs(v) >= 100 ? v.toFixed(0) : v.toFixed(v < 10 ? 2 : 1)
  return (
    <div className="legend">
      <div className="legend-head">
        <span>{label}</span>
        {onToggleSteps && (
          <button className={`btn mini ${steps ? 'active' : ''}`} onClick={onToggleSteps}
                  title="Hard steps are easier to read against limits; soft is better for presentation">
            {steps ? 'steps' : 'soft'}
          </button>
        )}
      </div>
      <div className="legend-bar" style={{ background: gradientCSS(steps ? STEPS : 0) }}>
        {tPos != null && tPos >= 0 && tPos <= 100 && (
          <span className="legend-threshold" style={{ left: `${tPos}%` }}
                title={`${thresholdLabel || 'threshold'}: ${fmt(threshold)} ${unit}`} />
        )}
      </div>
      <div className="legend-ticks">
        <span>{fmt(min)}</span>
        {tPos != null && <span className="legend-tlabel">{thresholdLabel || 'limit'} {fmt(threshold)}</span>}
        <span>{fmt(max)} {unit}</span>
      </div>
      {children}
    </div>
  )
}
