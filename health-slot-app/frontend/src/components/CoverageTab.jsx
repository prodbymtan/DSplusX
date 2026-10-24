// Coverage Countdown (patient view, H2).
//
// Tracks the user's next MassHealth renewal date so coverage doesn't quietly
// lapse. Relay NEVER decides eligibility — it only reminds, explains, and routes
// (decision #18). The renewal date lives CLIENT-SIDE ONLY in localStorage
// (decisions #11/#16): there is no backend table, endpoint, or network call for
// it, and this file deliberately does not import services/api.js.
//
// Hard rules honored here:
//   - exact line "MassHealth decides eligibility. This is a reminder, not a decision."
//   - NO MassHealth ID number field anywhere (decision #20)
//   - in-app reminders only, no SMS (decision #19)
//   - link out to mass.gov/masshealth, do not copy official text
//   - reminders use TEXT labels, never color alone (WCAG 2.1 AA)

import { useEffect, useId, useState } from 'react'
import { useNow } from '../hooks'

const STORAGE_KEY = 'relay.coverage.renewalDate'
const DAY_MS = 24 * 60 * 60 * 1000

// YYYY-MM-DD for a date `days` out from today (local time).
function isoDaysFromToday(days) {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  d.setDate(d.getDate() + days)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

// Whole days from `now` (ms) until the start of the renewal day (local midnight).
function daysUntil(renewalDate, now) {
  if (!renewalDate) return null
  const [y, m, d] = renewalDate.split('-').map(Number)
  if (!y || !m || !d) return null
  const target = new Date(y, m - 1, d, 0, 0, 0, 0).getTime()
  const todayStart = new Date(now)
  todayStart.setHours(0, 0, 0, 0)
  return Math.round((target - todayStart.getTime()) / DAY_MS)
}

// Human countdown text that never relies on color.
function countdownLabel(days) {
  if (days == null) return 'No renewal date set yet.'
  if (days > 1) return `Renewal in ${days} days`
  if (days === 1) return 'Renewal in 1 day'
  if (days === 0) return 'Renewal is today'
  if (days === -1) return 'Renewal was 1 day ago'
  return `Renewal was ${Math.abs(days)} days ago`
}

const REMINDER_MARKS = [30, 14, 7]

export default function CoverageTab() {
  const dateId = useId()
  const dateHintId = useId()
  const [renewalDate, setRenewalDate] = useState('')
  const now = useNow()

  // On mount: read the saved date, or default to ~21 days out (Maria's demo) and persist it.
  useEffect(() => {
    let saved = null
    try {
      saved = window.localStorage.getItem(STORAGE_KEY)
    } catch {
      /* storage unavailable (private mode); fall back to the in-memory default */
    }
    if (saved) {
      setRenewalDate(saved)
    } else {
      const def = isoDaysFromToday(21)
      setRenewalDate(def)
      try {
        window.localStorage.setItem(STORAGE_KEY, def)
      } catch {
        /* ignore: date still works in-memory for the session */
      }
    }
  }, [])

  const onDateChange = (e) => {
    const next = e.target.value
    setRenewalDate(next)
    try {
      window.localStorage.setItem(STORAGE_KEY, next)
    } catch {
      /* ignore: keep the value in state even if we can't persist it */
    }
  }

  const days = daysUntil(renewalDate, now)

  return (
    <div className="coverage">
      <h2 className="coverage-title">Coverage countdown</h2>
      <p className="coverage-persona">Maria Santos · Fictional demo persona</p>

      <div className="field coverage-field">
        <label htmlFor={dateId}>Next MassHealth renewal date</label>
        <input
          id={dateId}
          type="date"
          value={renewalDate}
          onChange={onDateChange}
          aria-describedby={dateHintId}
        />
        <p id={dateHintId} className="coverage-hint">
          Stored only on this device. We never send it anywhere.
        </p>
      </div>

      <div className="coverage-count" role="status" aria-live="polite">
        {countdownLabel(days)}
      </div>

      <section className="coverage-reminders" aria-label="Renewal reminders">
        <h3>Reminders</h3>
        <ul>
          {REMINDER_MARKS.map((mark) => {
            const reached = days != null && days <= mark
            return (
              <li key={mark} className={`coverage-reminder ${reached ? 'reached' : 'upcoming'}`}>
                <span className="coverage-reminder-mark">{mark}-day reminder:</span>{' '}
                <span className="coverage-reminder-state">{reached ? 'reached' : 'not yet'}</span>
              </li>
            )
          })}
        </ul>
        <p className="coverage-nosms">In-app reminders only. We don&apos;t send texts.</p>
      </section>

      <section className="coverage-explainer" aria-label="What to expect">
        <h3>What to expect</h3>
        <p>
          MassHealth mails a renewal packet before your date. Review it, update anything that
          changed (address, income, household), and return it by the deadline so your coverage
          keeps going. If you miss it, you may be able to reinstate coverage within a short window.
        </p>
        <p>
          Some members will need to renew every 6 months starting in 2027.
        </p>
        <p>
          <a
            href="https://www.mass.gov/masshealth"
            target="_blank"
            rel="noopener noreferrer"
          >
            Open the official MassHealth page (mass.gov/masshealth)
          </a>
        </p>
      </section>

      <p className="coverage-disclaimer">
        MassHealth decides eligibility. This is a reminder, not a decision.
      </p>
    </div>
  )
}
