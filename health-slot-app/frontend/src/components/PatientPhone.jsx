import { useCallback, useEffect, useState } from 'react'
import { api } from '../services/api'
import { connectSocket } from '../services/socket'
import { fmtCountdown, remaining, useNow } from '../hooks'

const OUTCOME = {
  booked: { text: (t) => `Booked for ${t}. Head over now.`, cls: 'ok' },
  taken: { text: (t) => `The ${t} slot was taken by someone else`, cls: 'muted' },
  expired: { text: (t) => `The ${t} offer expired`, cls: 'muted' },
}

export default function PatientPhone({ patientId, resetKey }) {
  const [state, setState] = useState(null)
  const [receivedAt, setReceivedAt] = useState(Date.now())
  const [connected, setConnected] = useState(false)
  const [notice, setNotice] = useState(null)
  const [busy, setBusy] = useState(false)
  const now = useNow()

  const refresh = useCallback(async () => {
    try {
      const s = await api.patientState(patientId)
      setState(s)
      setReceivedAt(Date.now())
    } catch {
      /* backend restarting; the socket reconnect will trigger another refresh */
    }
  }, [patientId])

  useEffect(() => {
    refresh()
    return connectSocket(
      `/ws/patients/${patientId}`,
      (msg) => {
        // The server state (history) now explains what happened; drop any old error.
        if (msg.type !== 'hello') setNotice(null)
        refresh()
      },
      (ok) => {
        setConnected(ok)
        if (ok) refresh()
      },
    )
  }, [patientId, refresh])

  useEffect(() => {
    setNotice(null)
    refresh()
  }, [resetKey, refresh])

  if (!state) return <div className="phone">Connecting…</div>
  const p = state.patient
  const offers = state.offers.filter((o) => remaining(o.seconds_left, receivedAt, now) > 0)
  const last = state.history[0]

  const claim = async (slotId) => {
    setBusy(true)
    try {
      await api.claim(slotId, patientId)
      setNotice(null)
    } catch (e) {
      setNotice({ text: e.message, cls: 'warn' })
    } finally {
      setBusy(false)
      refresh()
    }
  }

  const toggle = async () => {
    await api.setAvailable(patientId, !p.is_available)
    refresh()
  }

  return (
    <div className={`phone ${offers.length ? 'has-offer' : ''}`}>
      <div className="phone-top">
        <div>
          <div className="name">{p.name}</div>
          <div className="muted small">
            {p.distance_miles} mi away · travels ≤ {p.radius_miles} mi ·{' '}
            {p.insurance === 'NO_INSURANCE' ? 'Uninsured' : p.insurance}
          </div>
        </div>
        <span className={`conn ${connected ? 'on' : 'off'}`} title={connected ? 'Live' : 'Reconnecting'} />
      </div>

      {offers.map((o) => (
        <div key={o.slot_id} className="offer">
          <div className="offer-title">Opening today at {o.time_label}</div>
          <div className="muted small">
            {o.clinic} · {o.distance_miles} mi{o.round > 0 ? ' · radius widened' : ''}
          </div>
          <div className="offer-row">
            <button className="primary" disabled={busy} onClick={() => claim(o.slot_id)}>
              Claim
            </button>
            <span className="countdown">{fmtCountdown(remaining(o.seconds_left, receivedAt, now))}</span>
          </div>
        </div>
      ))}

      {!offers.length && (
        <div className="phone-body">
          {notice ? (
            <div className={notice.cls}>{notice.text}</div>
          ) : last ? (
            <div className={OUTCOME[last.outcome].cls}>{OUTCOME[last.outcome].text(last.time_label)}</div>
          ) : p.is_available ? (
            <div className="muted">
              {p.eligible_now ? 'Standby on. Waiting for an opening.' : `Standby on · not eligible now: ${p.eligibility_reason}`}
            </div>
          ) : (
            <div className="muted">Standby paused</div>
          )}
        </div>
      )}

      <label className="toggle">
        <input type="checkbox" checked={p.is_available} onChange={toggle} /> Standby
      </label>
    </div>
  )
}
