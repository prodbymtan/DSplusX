// Patient portal "Health" view: a read-only summary of the patient's recorded
// wearable (Empatica E4) sessions. Not diagnostic — it just shows what the
// wristband measured: session durations, heart-rate range + trend, skin temp,
// electrodermal activity and relative movement.

import { useEffect, useState } from 'react'
import { api } from '../services/api'

function Sparkline({ points, min, max }) {
  if (!points || points.length < 2) return null
  const w = 200
  const h = 44
  const lo = min ?? Math.min(...points)
  const hi = max ?? Math.max(...points)
  const span = hi - lo || 1
  const step = w / (points.length - 1)
  const d = points
    .map((v, i) => `${i === 0 ? 'M' : 'L'}${(i * step).toFixed(1)} ${(h - ((v - lo) / span) * h).toFixed(1)}`)
    .join(' ')
  return (
    <svg className="spark" width={w} height={h} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" aria-hidden="true">
      <path d={d} fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  )
}

const ICON = { 'Stress session': '🧠', 'Aerobic workout': '🏃', 'Anaerobic workout': '🏋️' }

export default function WearablePanel({ patientId }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let alive = true
    api
      .wearable(patientId)
      .then((d) => alive && setData(d))
      .catch((e) => alive && setError(e.message))
    return () => {
      alive = false
    }
  }, [patientId])

  if (error) return <div className="pp-idle"><div className="muted">Couldn’t load wearable data: {error}</div></div>
  if (!data) return <div className="pp-idle"><div className="muted">Loading your wearable summary…</div></div>
  if (!data.available) {
    return (
      <div className="pp-idle">
        <div className="pulse-dot">⌚</div>
        <div className="muted">No wearable sessions recorded yet.</div>
      </div>
    )
  }

  const { info, rollup, sessions } = data

  return (
    <div className="wearable">
      <div className="wear-intro">
        <div className="wear-title">Your wearable health</div>
        <div className="muted small">Last {rollup.sessions_count} recorded sessions from your wristband</div>
      </div>

      {info && (info.age || info.height_cm) && (
        <div className="wear-profile muted small">
          {[info.gender, info.age && `${info.age} yrs`, info.height_cm && `${info.height_cm} cm`, info.weight_kg && `${info.weight_kg} kg`]
            .filter(Boolean)
            .join(' · ')}
        </div>
      )}

      <div className="wear-rollup">
        <div className="wear-stat">
          <div className="ws-value">{rollup.avg_hr ?? '–'}<span className="ws-unit"> bpm</span></div>
          <div className="ws-label">Avg heart rate</div>
        </div>
        <div className="wear-stat">
          <div className="ws-value">{rollup.peak_hr ?? '–'}<span className="ws-unit"> bpm</span></div>
          <div className="ws-label">Peak</div>
        </div>
        <div className="wear-stat">
          <div className="ws-value">{rollup.total_active_min ?? '–'}<span className="ws-unit"> min</span></div>
          <div className="ws-label">Active time</div>
        </div>
      </div>

      <div className="wear-sessions">
        {sessions.map((s, i) => (
          <div className="wear-card" key={i}>
            <div className="wc-head">
              <span className="wc-ico">{ICON[s.label] || '⌚'}</span>
              <div className="wc-title">
                <div className="wc-name">{s.label}</div>
                <div className="muted small">{s.date_shown} · {s.duration_min} min</div>
              </div>
            </div>

            <Sparkline points={s.hr_trend} min={s.hr_min} max={s.hr_max} />
            <div className="wc-hr muted small">
              Heart rate {s.hr_min}–{s.hr_max} bpm (avg {s.hr_avg})
            </div>

            <div className="wc-metrics">
              {s.temp_avg_c != null && <span>🌡️ {s.temp_avg_c}°C skin</span>}
              {s.eda_avg_us != null && <span>💧 {s.eda_avg_us} µS</span>}
              {s.movement != null && <span>📈 {s.movement} g movement</span>}
            </div>
          </div>
        ))}
      </div>

      <div className="wear-note">
        {data.note} This is not medical advice; talk to your clinician about anything that concerns you.
      </div>
    </div>
  )
}
