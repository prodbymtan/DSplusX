// Map tab: who's nearby, the live search radius in real miles, and an animated
// "ripple" that pushes outward each round. The nurse can zoom in/out and widen
// the radius manually with "Increase radius".
//
// Offline SVG (no tiles / API keys). lat/lng is projected to miles around the clinic.

import { useEffect, useRef, useState } from 'react'
import { fmtCountdown, remaining, useNow } from '../hooks'

const W = 560
const H = 420
const CHAR_W = 5.0 // smaller hospital labels

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

function placeLabel(x, y, text, taken, gap = 8, charW = 6.2) {
  const w = text.length * charW
  const h = 12
  const candidates = [
    { x: x + gap, y: y - h / 2 },
    { x: x - gap - w, y: y - h / 2 },
    { x: x - w / 2, y: y + gap },
    { x: x - w / 2, y: y - gap - h },
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

function shorten(name, n = 18) {
  return name.length > n ? `${name.slice(0, n - 1)}…` : name
}

export default function ClinicMap({ map, schedule, receivedAt, onExpand }) {
  const now = useNow()
  const [zoom, setZoom] = useState(1)
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState(null)
  const [sweepKey, setSweepKey] = useState(0)
  const lastMultiplier = useRef(0)

  const openAppt = schedule?.appointments.find((a) => a.slot?.status === 'open')
  const openSlot = openAppt?.slot || null
  const multiplier = openSlot ? openSlot.radius_multiplier : 0

  useEffect(() => {
    if (multiplier !== lastMultiplier.current) {
      lastMultiplier.current = multiplier
      if (multiplier > 0) setSweepKey((k) => k + 1)
    }
  }, [multiplier])

  if (!map) return <section className="card">Loading map…</section>

  const center = map.clinic
  const baseRadius = Math.max(1, ...map.patients.map((p) => p.radius_miles))
  const farthest = Math.max(1, ...map.patients.map((p) => milesFrom(p, center)))
  const offerRadiusMiles = openSlot ? baseRadius * (multiplier || 1) : 0

  // Fit everything, then apply the user's zoom.
  const fitExtent = Math.max(2.5, farthest * 1.25, offerRadiusMiles * 1.1)
  const extent = fitExtent / zoom
  const scale = Math.min(W, H) / 2 / extent
  const rings = [0.5, 1, 2, 3, 4, 6, 8, 10, 15].filter((r) => r <= extent * 1.35)

  const offered = new Set()
  if (openSlot) openSlot.offered.forEach((o) => offered.add(o.patient_id))

  const taken = [{ x: W / 2 - 9, y: H / 2 - 9, w: 18, h: 18 }]
  const pts = map.patients
    .map((p) => {
      const [x, y] = project(p.lat, p.lng, center, scale)
      return { ...p, x, y, miles: milesFrom(p, center) }
    })
    .filter((p) => p.x > 2 && p.x < W - 2 && p.y > 2 && p.y < H - 2)
  pts.forEach((p) => taken.push({ x: p.x - 7, y: p.y - 7, w: 14, h: 14 }))

  const hosp = (map.hospitals || [])
    .map((h) => {
      const [x, y] = project(h.lat, h.lng, center, scale)
      return { ...h, x, y }
    })
    .filter((h) => h.x > 4 && h.x < W - 4 && h.y > 4 && h.y < H - 4)
  hosp.forEach((h) => taken.push({ x: h.x - 4, y: h.y - 4, w: 8, h: 8 }))

  const ptLabels = pts.map((p) => placeLabel(p.x, p.y, p.name, taken, 8, 6.2))
  const hospLabels = hosp.map((h) => placeLabel(h.x, h.y, shorten(h.name), taken, 5, CHAR_W))
  const hiddenHospitals = hospLabels.filter((l) => !l).length

  const offerRadiusPx = offerRadiusMiles * scale
  const secondsLeft = openSlot ? remaining(openSlot.seconds_left, receivedAt, now) : 0
  const atMaxRadius = openSlot && openSlot.round >= 2 // RIPPLE_ROUNDS default is 2

  const pushRadius = async () => {
    if (!openSlot) return
    setBusy(true)
    setNote(null)
    try {
      await onExpand(openSlot.id)
    } catch (e) {
      setNote(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="card map">
      <header className="card-head">
        <div>
          <h2>Who’s in range</h2>
          <div className="muted small">
            {openSlot
              ? `Searching for ${openAppt.time_label} · ${fmtCountdown(secondsLeft)} until the radius widens on its own`
              : 'Release a slot on the Schedule tab to watch the search radius expand.'}
          </div>
        </div>
        <div className="legend small muted">
          <span><i className="lg clinic" /> Clinic</span>
          <span><i className="lg patient" /> Standby</span>
          <span><i className="lg offered" /> Notified</span>
          <span><i className="lg hospital" /> Hospital</span>
        </div>
      </header>

      <div className="map-toolbar">
        <div className="radius-readout">
          {openSlot ? (
            <>
              <span className="rr-label">Current search radius</span>
              <span className="rr-value">{offerRadiusMiles.toFixed(1)} mi</span>
              <span className="muted small">round {openSlot.round} of 2</span>
            </>
          ) : (
            <span className="muted small">No active search</span>
          )}
        </div>
        <div className="map-controls">
          <button
            className="primary"
            disabled={!openSlot || busy || atMaxRadius}
            onClick={pushRadius}
            title={!openSlot ? 'Release a slot first' : atMaxRadius ? 'Already at the widest radius' : 'Widen the search now'}
          >
            {atMaxRadius ? 'Radius maxed' : 'Increase radius'}
          </button>
          <div className="zoom-controls" role="group" aria-label="Zoom">
            <button onClick={() => setZoom((z) => Math.max(0.5, +(z / 1.3).toFixed(2)))} aria-label="Zoom out">–</button>
            <span className="zoom-level">{Math.round(zoom * 100)}%</span>
            <button onClick={() => setZoom((z) => Math.min(6, +(z * 1.3).toFixed(2)))} aria-label="Zoom in">+</button>
            <button className="ghost small" onClick={() => setZoom(1)}>Reset</button>
          </div>
        </div>
      </div>
      {note && <div className="error">{note}</div>}

      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Map of the clinic, standby patients, nearby hospitals and the current search radius">
        {rings.map((r) => (
          <g key={r}>
            <circle cx={W / 2} cy={H / 2} r={r * scale} className="ring" />
            <text x={W / 2 + r * scale * 0.71 + 3} y={H / 2 - r * scale * 0.71 - 3} className="ring-label">
              {r} mi
            </text>
          </g>
        ))}

        {openSlot && offerRadiusPx > 0 && (
          <g key={sweepKey}>
            <circle cx={W / 2} cy={H / 2} r={offerRadiusPx} className="offer-area">
              <animate attributeName="r" from="0" to={offerRadiusPx} dur="0.9s" fill="freeze" calcMode="spline" keySplines="0.22 1 0.36 1" keyTimes="0;1" />
            </circle>
            <circle cx={W / 2} cy={H / 2} r={offerRadiusPx} className="offer-edge">
              <animate attributeName="r" from="0" to={offerRadiusPx} dur="0.9s" fill="freeze" calcMode="spline" keySplines="0.22 1 0.36 1" keyTimes="0;1" />
            </circle>
            {/* One outward pulse each time the radius grows, then it rests —
                purposeful (shows the search widening), not a decorative loop. */}
            <circle cx={W / 2} cy={H / 2} className="offer-pulse" fill="none">
              <animate attributeName="r" from={Math.max(6, offerRadiusPx * 0.25)} to={offerRadiusPx} dur="1.1s" begin="0s" fill="freeze" calcMode="spline" keySplines="0.22 1 0.36 1" keyTimes="0;1" />
              <animate attributeName="opacity" from="0.55" to="0" dur="1.1s" begin="0s" fill="freeze" />
            </circle>
          </g>
        )}

        {hosp.map((h, i) => (
          <g key={h.name}>
            <title>{`${h.name} · ${h.municipality || ''} · ${h.distance_miles} mi`}</title>
            <path d={`M${h.x - 4} ${h.y}H${h.x + 4}M${h.x} ${h.y - 4}V${h.y + 4}`} className="hospital" />
            {hospLabels[i] && (
              <text x={hospLabels[i].x} y={hospLabels[i].y} className="hosp-label">{shorten(h.name)}</text>
            )}
          </g>
        ))}

        <rect x={W / 2 - 7} y={H / 2 - 7} width={14} height={14} rx={3} className="clinic-mark" />

        {pts.map((p, i) => {
          const isOffered = offered.has(p.id)
          const cls = isOffered ? 'patient offered' : p.is_available ? 'patient' : 'patient paused'
          return (
            <g key={p.id}>
              <title>{`${p.name}: ${p.miles.toFixed(2)} mi away, travels up to ${p.radius_miles} mi`}</title>
              {isOffered && <circle cx={p.x} cy={p.y} r={11} className="offered-halo" />}
              <circle cx={p.x} cy={p.y} r={6} className={cls} />
              {ptLabels[i] && (
                <text x={ptLabels[i].x} y={ptLabels[i].y} className="pt-label">{p.name}</text>
              )}
            </g>
          )
        })}
      </svg>

      <div className="muted small">
        Patients are synthetic (Synthea, Massachusetts). Hospitals are real licensed facilities (MassGIS / MA DPH)
        {hiddenHospitals ? `; ${hiddenHospitals} more off-screen or hidden, hover the crosses for names` : ''}.
      </div>
    </section>
  )
}
