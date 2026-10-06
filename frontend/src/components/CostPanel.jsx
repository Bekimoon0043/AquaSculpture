import useBriefStore from '../store/briefStore'

const fmt = (v) => `$${v.toLocaleString('en-US', { maximumFractionDigits: 0 })}`

export default function CostPanel() {
  const engineering = useBriefStore((s) => s.engineering)
  if (!engineering) {
    return <div style={styles.panel}><h2 style={styles.heading}>Cost</h2>
      <p style={styles.empty}>No run yet — press Generate.</p></div>
  }
  const cost = engineering.cost

  return (
    <div style={styles.panel}>
      <h2 style={styles.heading}>Cost</h2>
      {cost.sections.map((s) => (
        <div key={s.key}>
          <div style={styles.section}>
            <span>{s.label}</span>
            <span>{fmt(s.amount)}</span>
          </div>
          {s.items.map((item, i) => (
            <div key={i} style={styles.item}>
              <span>{item.label}</span>
              <span>{fmt(item.amount)}</span>
            </div>
          ))}
        </div>
      ))}
      <div style={styles.section}><span>SUBTOTAL</span><span>{fmt(cost.subtotal_usd)}</span></div>
      <div style={styles.item}><span>Contingency {cost.contingency_pct}%</span><span>{fmt(cost.contingency_usd)}</span></div>
      <div style={styles.item}><span>Margin {cost.margin_pct}%</span><span>{fmt(cost.margin_usd)}</span></div>
      <div style={styles.total}><span>TOTAL</span><span>{fmt(cost.total_usd)}</span></div>
      {cost.budget_usd != null && (
        <div style={{ ...styles.budget, color: cost.over_budget ? '#ff6b6b' : '#7dd87d' }}>
          Budget {fmt(cost.budget_usd)} — {cost.over_budget
            ? `OVER by ${fmt(cost.budget_delta_usd)}`
            : `under by ${fmt(-cost.budget_delta_usd)}`}
        </div>
      )}
      <div style={styles.item}>
        <span>Annual opex (energy)</span><span>{fmt(cost.opex_annual_usd)}/yr</span>
      </div>
    </div>
  )
}

const styles = {
  panel: { padding: '12px', overflow: 'auto' },
  heading: { margin: 0, fontSize: '14px', color: '#ccc', textTransform: 'uppercase' },
  section: {
    display: 'flex', justifyContent: 'space-between', fontSize: '13px',
    fontWeight: 700, marginTop: '10px', color: '#7da7ff',
  },
  item: {
    display: 'flex', justifyContent: 'space-between', fontSize: '12px',
    color: '#bbb', padding: '1px 0 1px 10px',
  },
  total: {
    display: 'flex', justifyContent: 'space-between', fontSize: '14px',
    fontWeight: 700, marginTop: '8px', borderTop: '1px solid #333', paddingTop: '6px',
  },
  budget: { fontSize: '12px', marginTop: '4px' },
  empty: { color: '#666', fontSize: '13px' },
}
