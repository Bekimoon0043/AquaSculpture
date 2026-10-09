import { useEffect, useState } from 'react'
import useBriefStore from '../store/briefStore'
import { FAMILIES } from '../families'

// Structured brief editor (nTop/Grasshopper lesson): the parameter form is
// generated from the generator signatures (/api/geometry/families), every
// control edits the brief in place and schedules a live engineering run.
const MATERIALS = ['stainless_304', 'stainless_316l', 'ss2205_duplex', 'mild_steel',
  'bronze', 'brass', 'grc', 'fiberglass', 'corten_steel', 'aluminum']
const FINISHES = ['mirror_polish_8', 'mirror', 'brushed', 'hairline', 'textured',
  'hammered', 'polished', 'patina', 'painted']
const BASIN_SHAPES = ['circular', 'rectangular', 'elliptical', 'polygonal']
const OVERFLOWS = ['perimeter_weir', 'slot_overflow', 'skimmer', 'none']
const FEATURE_TYPES = ['still_basin', 'bubbler_field', 'foam_jet_field', 'water_sheet',
  'curtain_from_sculpture', 'curtain_between_elements', 'rain_curtain',
  'perimeter_mist', 'perimeter_weir']
const WIND_ZONES = ['low', 'moderate', 'high', 'extreme']

const pretty = (s) => s.replace(/_m$/, ' (m)').replace(/_deg$/, ' (deg)').replace(/_/g, ' ')

function Field({ label, children }) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      {children}
    </label>
  )
}

function NumberField({ label, value, onChange, step = 0.1, min, max }) {
  return (
    <Field label={label}>
      <input type="number" value={value ?? ''} step={step} min={min} max={max}
             onChange={(e) => e.target.value !== '' && onChange(+e.target.value)} />
    </Field>
  )
}

function SelectField({ label, value, options, onChange }) {
  return (
    <Field label={label}>
      <select value={value ?? ''} onChange={(e) => onChange(e.target.value)}>
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </Field>
  )
}

function CheckField({ label, value, onChange }) {
  return (
    <label className="field check">
      <input type="checkbox" checked={!!value} onChange={(e) => onChange(e.target.checked)} />
      <span className="field-label">{label}</span>
    </label>
  )
}

// Slider + number pair for a generated numeric parameter.
function ParamControl({ meta, value, onChange }) {
  const v = value ?? meta.default
  if (meta.type === 'bool') return <CheckField label={pretty(meta.name)} value={v} onChange={onChange} />
  if (meta.type === 'str') {
    if (meta.choices) return <SelectField label={pretty(meta.name)} value={v} options={meta.choices} onChange={onChange} />
    return <Field label={pretty(meta.name)}><input type="text" value={v} onChange={(e) => onChange(e.target.value)} /></Field>
  }
  const parse = meta.type === 'int' ? (x) => Math.round(+x) : (x) => +x
  return (
    <div className="field param">
      <div className="param-head">
        <span className="field-label">{pretty(meta.name)}</span>
        <input type="number" value={v} step={meta.step} min={meta.min} max={meta.max}
               onChange={(e) => e.target.value !== '' && onChange(parse(e.target.value))} />
      </div>
      <input type="range" value={v} step={meta.step} min={meta.min} max={meta.max}
             onChange={(e) => onChange(parse(e.target.value))} />
    </div>
  )
}

export default function BriefEditor() {
  const brief = useBriefStore((s) => s.brief)
  const catalog = useBriefStore((s) => s.catalog)
  const loadCatalog = useBriefStore((s) => s.loadCatalog)
  const updateBrief = useBriefStore((s) => s.updateBrief)
  const changeFamily = useBriefStore((s) => s.changeFamily)
  const [raw, setRaw] = useState(false)

  useEffect(() => { loadCatalog() }, [loadCatalog])

  if (!brief) {
    return <div className="panel"><h2>Design Brief</h2>
      <p className="hint">No brief yet — press Generate or describe a design.</p></div>
  }

  const sc = brief.sculpture || {}
  const water = brief.water || {}
  const basin = water.basin
  const features = water.features || []
  const lighting = brief.lighting || {}
  const cons = brief.constraints || {}
  const project = brief.project || {}
  const params = catalog?.[sc.family] || []
  const set = updateBrief

  return (
    <div className="panel brief-form">
      <div className="panel-head">
        <h2>Design Brief</h2>
        <button className={`btn mini ${raw ? 'active' : ''}`} onClick={() => setRaw((r) => !r)}>JSON</button>
      </div>
      {raw ? (
        <pre>{JSON.stringify(brief, null, 2)}</pre>
      ) : (
        <>
          <h3 className="form-section">Project</h3>
          <Field label="name"><input type="text" value={project.name || ''} onChange={(e) => set('project.name', e.target.value)} /></Field>
          <Field label="site"><input type="text" value={project.site || ''} onChange={(e) => set('project.site', e.target.value)} /></Field>
          <NumberField label="budget (USD)" value={project.budget_usd} step={1000} min={0} onChange={(v) => set('project.budget_usd', v)} />

          <h3 className="form-section">Sculpture</h3>
          <SelectField label="family" value={sc.family} options={Object.keys(FAMILIES)} onChange={changeFamily} />
          <NumberField label="height (m)" value={sc.height_m} step={0.1} min={0.3} onChange={(v) => set('sculpture.height_m', v)} />
          <SelectField label="material" value={sc.material} options={MATERIALS} onChange={(v) => set('sculpture.material', v)} />
          <SelectField label="finish" value={sc.finish} options={FINISHES} onChange={(v) => set('sculpture.finish', v)} />

          <h3 className="form-section">Parameters <span className="hint">{FAMILIES[sc.family]?.label}</span></h3>
          {params.length === 0 && <p className="hint">This family has no free parameters.</p>}
          {params.map((meta) => (
            <ParamControl key={meta.name} meta={meta}
                          value={sc.parameters?.[meta.name]}
                          onChange={(v) => set(`sculpture.parameters.${meta.name}`, v)} />
          ))}

          <h3 className="form-section">Water</h3>
          {basin ? (
            <>
              <SelectField label="basin shape" value={basin.shape} options={BASIN_SHAPES} onChange={(v) => set('water.basin.shape', v)} />
              {basin.shape === 'rectangular' ? (
                <>
                  <NumberField label="length (m)" value={basin.length_m} step={0.1} min={0.5} onChange={(v) => set('water.basin.length_m', v)} />
                  <NumberField label="width (m)" value={basin.width_m} step={0.1} min={0.5} onChange={(v) => set('water.basin.width_m', v)} />
                </>
              ) : (
                <NumberField label="diameter (m)" value={basin.diameter_m} step={0.1} min={0.5} onChange={(v) => set('water.basin.diameter_m', v)} />
              )}
              <NumberField label="depth (m)" value={basin.depth_m} step={0.05} min={0.1} onChange={(v) => set('water.basin.depth_m', v)} />
              <Field label="basin material"><input type="text" value={basin.material || ''} onChange={(e) => set('water.basin.material', e.target.value)} /></Field>
              <SelectField label="overflow" value={basin.overflow || 'none'} options={OVERFLOWS} onChange={(v) => set('water.basin.overflow', v)} />
            </>
          ) : (
            <button className="btn" onClick={() => set('water.basin', { shape: 'circular', diameter_m: 6, depth_m: 0.45, material: 'black_granite', overflow: 'perimeter_weir' })}>
              Add basin
            </button>
          )}
          <div className="feature-list">
            {features.map((f, i) => (
              <div key={i} className="feature-row">
                <select value={f.type} onChange={(e) => set(`water.features.${i}.type`, e.target.value)}>
                  {FEATURE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
                <input type="number" min={1} step={1} value={f.count ?? ''} placeholder="n"
                       title="count" onChange={(e) => e.target.value !== '' && set(`water.features.${i}.count`, Math.round(+e.target.value))} />
                <button className="btn mini" title="Remove feature"
                        onClick={() => set('water.features', features.filter((_, j) => j !== i))}>x</button>
              </div>
            ))}
            <button className="btn mini" onClick={() => set('water.features', [...features, { type: 'bubbler_field', count: 6 }])}>
              + feature
            </button>
          </div>

          <h3 className="form-section">Lighting</h3>
          <NumberField label="sculpture uplights" value={lighting.sculpture_uplights ?? 0} step={1} min={0} onChange={(v) => set('lighting.sculpture_uplights', Math.round(v))} />
          <NumberField label="submersible RGB" value={lighting.submersible_rgb ?? 0} step={1} min={0} onChange={(v) => set('lighting.submersible_rgb', Math.round(v))} />
          <CheckField label="backlit perforation" value={lighting.backlit_perforation} onChange={(v) => set('lighting.backlit_perforation', v)} />

          <h3 className="form-section">Site constraints</h3>
          <SelectField label="wind zone" value={cons.wind_zone || 'moderate'} options={WIND_ZONES} onChange={(v) => set('constraints.wind_zone', v)} />
          <CheckField label="indoor" value={cons.indoor} onChange={(v) => set('constraints.indoor', v)} />
          <CheckField label="public access" value={cons.public_access} onChange={(v) => set('constraints.public_access', v)} />
          <NumberField label="site wind (m/s, measured)" value={cons.site_wind_ms} step={1} min={0} onChange={(v) => set('constraints.site_wind_ms', v)} />
          <NumberField label="max height (m)" value={cons.max_height_m} step={0.5} min={0} onChange={(v) => set('constraints.max_height_m', v)} />
        </>
      )}
    </div>
  )
}
