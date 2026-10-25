// Schedule tab: today's appointments, who cancelled / didn't show, a release
// control, a preview of who would be notified first, and the live refill +
// radius-expansion status. No-show risk is intentionally not shown here (the
// model story lives in the Data tab).

import { useState } from 'react'
import { motion, useReducedMotion } from 'motion/react'
import { fmtCountdown, remaining, useNow } from '../hooks'
import { CalendarIcon, CheckIcon } from './icons'

const REASON = { no_show: 'No-show', late: 'No-show', cancelled: 'Cancelled', unconfirmed: 'Released' }

// Who's first in line if a slot opens: closest eligible patient first.
function nextInLine(patients) {
  return patients
    .filter((p) => p.eligible_now)
    .sort((a, b) => a.distance_miles - b.distance_miles)
}

function SlotStatus({ slot, receivedAt, now }) {
  if (slot.status === 'open') {
    const names = slot.offered.map((o) => o.name).join(', ')
    return (
      <div className="slot-status open">
        <span className="dot pulse" /> Notifying{slot.round > 0 ? ` · radius widened ×${slot.radius_multiplier}` : ''} ·{' '}
        {fmtCountdown(remaining(slot.seconds_left, receivedAt, now))}
        <div className="muted small">{names ? `Sent to ${names}` : 'Nobody in range yet, widening'}</div>
      </div>
    )
  }
  if (slot.status === 'booked') {
    return (
      <div className="slot-status booked">
        <span className="si"><CheckIcon size={15} /></span> Rebooked with {slot.booked_by}
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

export default function ClinicSchedule({ schedule, patients, receivedAt, onRelease, activity, lastBooked }) {
  const now = useNow()
  const reduce = useReducedMotion()
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

  const ranked = nextInLine(patients)
  const anyOpen = schedule.appointments.some((a) => a.slot?.status === 'open')

  return (
    <section className="card">
      <header className="card-head">
        <div>
          <h2>Today’s schedule</h2>
          <div className="muted small">{schedule.clinic?.name}</div>
        </div>
      </header>

      {lastBooked && (
        <div className="new-appt" key={lastBooked.id}>
          <span className="na-ico"><CalendarIcon size={18} /></span> New appointment booked — {lastBooked.text}
        </div>
      )}
      {error && <div className="error">{error}</div>}

      <div className="schedule">
        {schedule.appointments.map((a, i) => (
          <motion.div
            key={a.id}
            className={`sched-row ${a.status !== 'scheduled' ? 'released' : ''}`}
            initial={reduce ? false : { opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, delay: Math.min(i * 0.035, 0.4), ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="time">{a.time_label}</div>
            <div className="who">
              <div>{a.patient_label}</div>
              <div className="muted small">Age {a.age} · {a.duration_min} min visit</div>
            </div>
            <div className="action">
              {a.status === 'scheduled' ? (
                <>
                  <div className="buttons">
                    <button disabled={busy === a.id} onClick={() => release(a.id, 'no_show')} className="primary">
                      Mark no-show
                    </button>
                    <button disabled={busy === a.id} onClick={() => release(a.id, 'cancelled')} className="ghost">
                      Cancelled
                    </button>
                  </div>
                  <div className="muted release-note">
                    A patient 20+ minutes late is automatically marked a no-show.
                  </div>
                </>
              ) : (
                <div>
                  <div className="muted small">{REASON[a.status] || 'Released'}</div>
                  {a.slot && <SlotStatus slot={a.slot} receivedAt={receivedAt} now={now} />}
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      {!anyOpen && ranked.length > 0 && (
        <div className="next-in-line">
          <div className="nil-label">Next in line if you release a slot</div>
          {ranked.slice(0, 3).map((p, i) => (
            <div className="nil-row" key={p.id}>
              <span>
                <span className="nil-name">{p.name}</span>{' '}
                <span className="muted small">· {p.distance_miles} mi away</span>
              </span>
              {i === 0 ? <span className="nil-badge">Notified first</span> : <span className="muted small">#{i + 1}</span>}
            </div>
          ))}
          <div className="muted small" style={{ marginTop: 8 }}>
            Closest patients first. Everyone in range is notified at once; the first to accept gets it.
          </div>
        </div>
      )}

      <div className="activity activity-big">
        <h3>Activity</h3>
        {activity.length === 0 ? (
          <div className="muted">Release a slot to start matching it to nearby standby patients. Live updates will appear here.</div>
        ) : (
          <ul>
            {activity.map((e) => (
              <li key={e.id}>
                <span className="act-time">{e.time}</span>
                <span className="act-text">{e.text}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
