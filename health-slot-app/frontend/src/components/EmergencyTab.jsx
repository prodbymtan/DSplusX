// Emergency Mode (patient view).
//
// EMTALA / No Surprises Act (decision #14): emergency care never depends on
// insurance, so there is deliberately NO insurance input here. We show the
// nearest emergency department, its straight-line distance, a large keyboard-
// accessible Call 911 button, and a verbatim reassurance line.

import { useCallback, useEffect, useState } from 'react'
import { api } from '../services/api'

export default function EmergencyTab({ lat, lng }) {
  const [er, setEr] = useState(null)
  const [status, setStatus] = useState('loading') // 'loading' | 'ready' | 'error'

  const findNearest = useCallback(async () => {
    setStatus('loading')
    try {
      const res = await api.nearestEr(lat, lng)
      setEr(res.nearest)
      setStatus('ready')
    } catch {
      setStatus('error')
    }
  }, [lat, lng])

  useEffect(() => {
    findNearest()
  }, [findNearest])

  return (
    <div className="emergency">
      <h2 className="emergency-title">Emergency</h2>

      <a className="call-911" href="tel:911" aria-label="Call 911 emergency services">
        Call 911
      </a>

      <p className="emergency-reassure">
        ERs must treat you regardless of insurance. You won&apos;t be denied emergency care.
      </p>

      <section className="emergency-er" aria-label="Nearest emergency room">
        <h3>Nearest emergency room</h3>

        {status === 'loading' && <p className="emergency-state">Finding the nearest ER…</p>}

        {status === 'error' && (
          <div className="emergency-state emergency-state-error" role="alert">
            <p>We couldn&apos;t load the nearest ER.</p>
            <button type="button" className="big" onClick={findNearest}>
              Find nearest ER
            </button>
          </div>
        )}

        {status === 'ready' && er && (
          <div>
            <p className="emergency-er-name">{er.name}</p>
            <p className="emergency-er-meta">
              {er.municipality}, {er.county} County
            </p>
            <p className="emergency-er-dist">
              {er.distance_miles} mi away (straight-line / approximate)
            </p>
            <button type="button" className="big" onClick={findNearest}>
              Find nearest ER
            </button>
          </div>
        )}

        {status === 'ready' && !er && (
          <p className="emergency-state" role="alert">
            No emergency room found. If this is an emergency, call 911 now.
          </p>
        )}
      </section>

      <p className="emergency-demo-note">
        Your location is a fictional demo value for patient #1, not a real position.
      </p>
    </div>
  )
}
