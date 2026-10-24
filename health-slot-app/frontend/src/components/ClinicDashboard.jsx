import { useState } from 'react'
import { fmtCountdown, pct, remaining, useNow } from '../hooks'

const REASON = { no_show: 'No-show', cancelled: 'Cancelled', unconfirmed: 'No reply' }

function SlotStatus({ slot, receivedAt, now }) {
  if (slot.status === 'open') {
    const names = slot.offered.map((o) => o.name).join(', ')
    return (
      <div className="slot-status open">
        <span className="dot pulse" /> Offering{slot.round > 0 ? ` · radius ×${slot.radius_multiplier}` : ''} ·{' '}
        {fmtCountdown(remaining(slot.seconds_left, receivedAt, now))}
        <div className="muted small">{names ? `Sent to ${names}` : 'Nobody eligible yet, widening radius'}</div>
      </div>
    )
  }
  if (slot.status === 'booked') {
    return (
      <div className="slot-status booked">
        Filled by {slot.booked_by}
        <div className="muted small">Slot recovered</div>
      </div>
    )
  }
  return (
    <div className="slot-status expired">
      Expired
      <div className="muted small">Nobody claimed it</div>
    </div>
  )
}

export default function ClinicDashboard({ schedule, receivedAt, onRelease, activity }) {
  const now = useNow()
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)

  if (!schedule) return <section className="card">Loading schedule…</section>

  const release = async (id, reason) => {
    setBusy(id)
    setError(null)
    try {
      await onRelease(id, reason)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(null)
    }
  }

  return (
    <section className="card clinic">
      <header className="card-head">
        <div>
          <h2>{schedule.clinic?.name}</h2>
          <div className="muted small">
            Today · risk from <code>{schedule.risk_source}</code> · high risk ≥ {pct(schedule.high_risk_threshold)}
          </div>
        </div>
      </header>
      {error && <div className="error">{error}</div>}
      <div className="schedule">
        {schedule.appointments.map((a) => (
          <div key={a.id} className={`row ${a.status !== 'scheduled' ? 'released' : ''}`}>
            <div className="time">{a.time_label}</div>
            <div className="who">
              <div>{a.patient_label}</div>
              <div className="muted small">
                Age {a.age} · booked {a.lead_days === 0 ? 'today' : `${a.lead_days}d ago`}
                {a.prior_appts > 0 ? ` · missed ${a.prior_noshows} of ${a.prior_appts} before` : ' · first visit'}
              </div>
            </div>
            <span className={`pill ${a.high_risk ? 'high' : 'low'}`} title="Predicted no-show probability">
              {pct(a.risk)} risk
            </span>
            <div className="action">
              {a.status === 'scheduled' ? (
                <>
                  {a.high_risk && <div className="muted small confirm-note">Asked to confirm</div>}
                  <div className="buttons">
                    {a.high_risk ? (
                      <button disabled={busy === a.id} onClick={() => release(a.id, 'unconfirmed')} className="primary">
                        No reply · release
                      </button>
                    ) : (
                      <button disabled={busy === a.id} onClick={() => release(a.id, 'no_show')}>
                        No-show
                      </button>
                    )}
                    <button disabled={busy === a.id} onClick={() => release(a.id, 'cancelled')} className="ghost">
                      Cancel
                    </button>
                  </div>
                </>
              ) : (
                <div>
                  <div className="muted small">{REASON[a.status]}</div>
                  {a.slot && <SlotStatus slot={a.slot} receivedAt={receivedAt} now={now} />}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      <div className="activity">
        <h3>Activity</h3>
        {activity.length === 0 ? (
          <div className="muted small">Release a slot to start. High-risk patients were asked to confirm.</div>
        ) : (
          <ul>
            {activity.map((e) => (
              <li key={e.id}>
                <span className="muted small">{e.time}</span> {e.text}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
