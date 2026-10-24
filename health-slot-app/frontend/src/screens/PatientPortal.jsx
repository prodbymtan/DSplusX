// The patient's phone. Deliberately minimal: a standby toggle, and when a slot
// is offered, a single notification popup with Accept / Decline and a countdown.
//
// Eligibility (travel radius, insurance, specialty, standby on) is enforced by the
// backend, so this patient only ever sees offers they can actually take. We feature
// one real dataset patient (Glenn A., patient id 1).

import { useCallback, useEffect, useState } from 'react'
import { api } from '../services/api'
import { connectSocket } from '../services/socket'
import { fmtCountdown, remaining, useNow } from '../hooks'

const FEATURED_PATIENT_ID = 1

function TimerRing({ secondsLeft, total }) {
  const r = 26
  const c = 2 * Math.PI * r
  const frac = total > 0 ? Math.max(0, Math.min(1, secondsLeft / total)) : 0
  return (
    <div className="timer-ring">
      <svg width="64" height="64" viewBox="0 0 64 64">
        <circle cx="32" cy="32" r={r} fill="none" stroke="var(--purple-100)" strokeWidth="6" />
        <circle
          cx="32" cy="32" r={r} fill="none" stroke="var(--accent)" strokeWidth="6" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - frac)} transform="rotate(-90 32 32)"
          style={{ transition: 'stroke-dashoffset 0.9s linear' }}
        />
      </svg>
      <div>
        <div className="count">{fmtCountdown(secondsLeft)}</div>
        <div className="count-sub">left to respond</div>
      </div>
    </div>
  )
}

export default function PatientPortal() {
  const [state, setState] = useState(null)
  const [receivedAt, setReceivedAt] = useState(Date.now())
  const [connected, setConnected] = useState(false)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState(null)
  const now = useNow()

  const refresh = useCallback(async () => {
    try {
      const s = await api.patientState(FEATURED_PATIENT_ID)
      setState(s)
      setReceivedAt(Date.now())
    } catch {
      /* backend restarting; socket reconnect will refresh again */
    }
  }, [])

  useEffect(() => {
    refresh()
    return connectSocket(
      `/ws/patients/${FEATURED_PATIENT_ID}`,
      (msg) => {
        if (msg.type !== 'hello') setNotice(null)
        refresh()
      },
      (ok) => {
        setConnected(ok)
        if (ok) refresh()
      },
    )
  }, [refresh])

  if (!state) {
    return (
      <div className="patient-stage">
        <div className="patient-phone">
          <div className="pp-body" style={{ justifyContent: 'center', textAlign: 'center', color: 'var(--muted)' }}>
            Connecting…
          </div>
        </div>
      </div>
    )
  }

  const p = state.patient
  const offer = state.offers.find((o) => remaining(o.seconds_left, receivedAt, now) > 0)
  const last = state.history[0]

  const accept = async () => {
    if (!offer) return
    setBusy(true)
    try {
      await api.claim(offer.slot_id, FEATURED_PATIENT_ID)
      setNotice(null)
    } catch (e) {
      setNotice({ cls: 'warn', text: e.message })
    } finally {
      setBusy(false)
      refresh()
    }
  }

  const decline = async () => {
    // Declining = turn standby off so no more offers come. Mirrors the backend's own
    // "booked -> standby off" behaviour; the current slot keeps rippling to others.
    setBusy(true)
    try {
      await api.setAvailable(FEATURED_PATIENT_ID, false)
    } finally {
      setBusy(false)
      refresh()
    }
  }

  const toggleStandby = async () => {
    await api.setAvailable(FEATURED_PATIENT_ID, !p.is_available)
    refresh()
  }

  return (
    <div className="patient-stage">
      <div className="patient-phone">
        <div className="pp-header">
          <div className="pp-hi">Signed in as</div>
          <div className="pp-name">{p.name}</div>
          <div className="pp-meta">
            <span>📍 {p.distance_miles} mi from clinic</span>
            <span>🚗 travels ≤ {p.radius_miles} mi</span>
            <span>🪪 {p.insurance === 'NO_INSURANCE' ? 'Uninsured' : p.insurance}</span>
          </div>
        </div>

        <div className="pp-body">
          <div className="pp-standby">
            <div>
              <div className="label">Standby for openings</div>
              <div className="sub">
                {p.is_available ? 'On — you can be offered last-minute slots' : 'Off — you won’t get offers'}
              </div>
            </div>
            <label className="switch">
              <input type="checkbox" checked={p.is_available} onChange={toggleStandby} />
              <span className="track" />
            </label>
          </div>

          {offer ? (
            <div className="notif">
              <div className="notif-top">
                <span className="notif-bell">🔔</span> Appointment available
              </div>
              <h2>Today at {offer.time_label}</h2>
              <div className="where">{offer.clinic} · {offer.distance_miles} mi away</div>
              {offer.round > 0 && <div className="ring-note">Offered to you as the search widened</div>}

              <TimerRing
                secondsLeft={remaining(offer.seconds_left, receivedAt, now)}
                total={offer.seconds_left || 1}
              />

              {notice && <div className={notice.cls} style={{ marginBottom: 10 }}>{notice.text}</div>}

              <div className="notif-actions">
                <button className="ghost" disabled={busy} onClick={decline}>Decline</button>
                <button className="primary" disabled={busy} onClick={accept}>Accept</button>
              </div>
            </div>
          ) : notice ? (
            <div className="pp-result">
              <div className="big-ico">⚠️</div>
              <div className={notice.cls}>{notice.text}</div>
            </div>
          ) : last && last.outcome === 'booked' ? (
            <div className="pp-result booked">
              <div className="big-ico">✅</div>
              <h2>You’re booked for {last.time_label}</h2>
              <div className="muted">Head to {offer?.clinic || state.history[0].clinic}. See you soon.</div>
            </div>
          ) : last && last.outcome === 'taken' ? (
            <div className="pp-result">
              <div className="big-ico">⌛</div>
              <h2>Just missed it</h2>
              <div className="muted">The {last.time_label} slot was claimed by someone else.</div>
            </div>
          ) : last && last.outcome === 'expired' ? (
            <div className="pp-result">
              <div className="big-ico">⌛</div>
              <h2>Offer expired</h2>
              <div className="muted">The {last.time_label} slot wasn’t claimed in time.</div>
            </div>
          ) : (
            <div className="pp-idle">
              <div className="pulse-dot">🔔</div>
              {p.is_available ? (
                p.eligible_now ? (
                  <div>You’re on standby. We’ll ping you the moment a slot opens nearby.</div>
                ) : (
                  <div>You’re on standby, but not eligible right now: {p.eligibility_reason}.</div>
                )
              ) : (
                <div>Standby is off. Turn it on to receive offers.</div>
              )}
            </div>
          )}
        </div>

        <div className="pp-foot">
          <span className={`conn ${connected ? 'on' : 'off'}`} /> {connected ? 'Live' : 'Reconnecting…'} · Synthetic patient (Synthea)
        </div>
      </div>
    </div>
  )
}
