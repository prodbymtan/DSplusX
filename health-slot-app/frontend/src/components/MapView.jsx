// Offline SVG map: no tiles, no API keys, works on any Wi-Fi.
// Projects lat/lng to miles around the clinic. Labels are placed greedily so they don't overlap.

const W = 520
const H = 360
const CHAR_W = 6.2 // approx px per character at 11px

function project(lat, lng, center, scale) {
  const dx = (lng - center.lng) * 69.17 * Math.cos((center.lat * Math.PI) / 180)
  const dy = (lat - center.lat) * 69.0
  return [W / 2 + dx * scale, H / 2 - dy * scale]
}

function milesFrom(p, c) {
  const dx = (p.lng - c.lng) * 69.17 * Math.cos((c.lat * Math.PI) / 180)
  const dy = (p.lat - c.lat) * 69.0
  return Math.hypot(dx, dy)
}

const overlaps = (a, b) => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h

// Try right, left, below, above; return the first box that doesn't collide (or null).
function placeLabel(x, y, text, taken, gap = 8) {
  const w = text.length * CHAR_W
  const h = 13
  const candidates = [
    { x: x + gap, y: y - h / 2, anchor: 'start' },
    { x: x - gap - w, y: y - h / 2, anchor: 'start' },
    { x: x - w / 2, y: y + gap, anchor: 'start' },
    { x: x - w / 2, y: y - gap - h, anchor: 'start' },
  ]
  for (const c of candidates) {
    const box = { x: c.x, y: c.y, w, h }
    if (box.x < 2 || box.x + w > W - 2 || box.y < 2 || box.y + h > H - 2) continue
    if (!taken.some((t) => overlaps(box, t))) {
      taken.push(box)
      return { x: c.x, y: c.y + h - 3 }
    }
  }
  return null
}

export default function MapView({ map, schedule }) {
  if (!map) return null
  const center = map.clinic
  const farthest = Math.max(1, ...map.patients.map((p) => milesFrom(p, center)))
  const extent = Math.max(2.5, farthest * 1.3) // miles from center to the shorter edge
  const scale = Math.min(W, H) / 2 / extent
  const rings = [1, 2, 3, 4, 6, 8].filter((r) => r <= extent * 1.35)

  // Which patients currently hold an open offer?
  const offered = new Set()
  schedule?.appointments.forEach((a) => {
    if (a.slot?.status === 'open') a.slot.offered.forEach((o) => offered.add(o.patient_id))
  })

  const taken = [{ x: W / 2 - 9, y: H / 2 - 9, w: 18, h: 18 }] // clinic marker
  const pts = map.patients.map((p) => {
    const [x, y] = project(p.lat, p.lng, center, scale)
    taken.push({ x: x - 7, y: y - 7, w: 14, h: 14 })
    return { ...p, x, y }
  })
  const hosp = map.hospitals
    .map((h) => {
      const [x, y] = project(h.lat, h.lng, center, scale)
      return { ...h, x, y }
    })
    .filter((h) => h.x > 4 && h.x < W - 4 && h.y > 4 && h.y < H - 4)
  hosp.forEach((h) => taken.push({ x: h.x - 4, y: h.y - 4, w: 8, h: 8 }))

  // Patient labels first (most important), then hospital labels where they fit.
  const ptLabels = pts.map((p) => placeLabel(p.x, p.y, p.name, taken))
  const hospLabels = hosp.map((h) => placeLabel(h.x, h.y, shorten(h.name), taken, 6))
  const hiddenHospitals = hospLabels.filter((l) => !l).length

  return (
    <section className="card map">
      <header className="card-head">
        <h2>Who's in range</h2>
        <div className="legend small muted">
          <span><i className="lg clinic" /> Clinic</span>
          <span><i className="lg patient" /> Standby</span>
          <span><i className="lg offered" /> Has offer</span>
          <span><i className="lg hospital" /> MA hospital</span>
        </div>
      </header>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Map of the clinic, standby patients and nearby hospitals">
        {rings.map((r) => (
          <g key={r}>
            <circle cx={W / 2} cy={H / 2} r={r * scale} className="ring" />
            <text x={W / 2 + r * scale * 0.71 + 3} y={H / 2 - r * scale * 0.71 - 3} className="ring-label">
              {r} mi
            </text>
          </g>
        ))}
        {hosp.map((h, i) => (
          <g key={h.name}>
            <title>{`${h.name} · ${h.municipality} · ${h.distance_miles} mi`}</title>
            <path d={`M${h.x - 4} ${h.y}H${h.x + 4}M${h.x} ${h.y - 4}V${h.y + 4}`} className="hospital" />
            {hospLabels[i] && (
              <text x={hospLabels[i].x} y={hospLabels[i].y} className="hosp-label">
                {shorten(h.name)}
              </text>
            )}
          </g>
        ))}
        <rect x={W / 2 - 7} y={H / 2 - 7} width={14} height={14} rx={3} className="clinic-mark" />
        {pts.map((p, i) => {
          const cls = offered.has(p.id) ? 'patient offered' : p.is_available ? 'patient' : 'patient paused'
          return (
            <g key={p.id}>
              <title>{`${p.name}: ${milesFrom(p, center).toFixed(2)} mi away, travels up to ${p.radius_miles} mi`}</title>
              <circle cx={p.x} cy={p.y} r={6} className={cls} />
              {ptLabels[i] && (
                <text x={ptLabels[i].x} y={ptLabels[i].y} className="pt-label">
                  {p.name}
                </text>
              )}
            </g>
          )
        })}
      </svg>
      <div className="muted small">
        Patients are synthetic (Synthea, Massachusetts). Hospitals are real licensed facilities (MassGIS / MA DPH)
        {hiddenHospitals ? `; ${hiddenHospitals} more nearby, hover the crosses for names` : ''}.
      </div>
    </section>
  )
}

function shorten(name) {
  return name.length > 24 ? `${name.slice(0, 23)}…` : name
}
