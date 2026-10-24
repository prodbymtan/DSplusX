import { useCallback, useEffect, useRef, useState } from 'react'
import ClinicDashboard from './components/ClinicDashboard'
import MapView from './components/MapView'
import MetricsPanel from './components/MetricsPanel'
import PatientPhone from './components/PatientPhone'
import { api } from './services/api'
import { connectSocket } from './services/socket'

export default function App() {
  const [schedule, setSchedule] = useState(null)
  const [receivedAt, setReceivedAt] = useState(Date.now())
  const [metrics, setMetrics] = useState(null)
  const [patients, setPatients] = useState([])
  const [map, setMap] = useState(null)
  const [activity, setActivity] = useState([])
  const [connected, setConnected] = useState(false)
  const [resetKey, setResetKey] = useState(0)
  const [error, setError] = useState(null)
  const nextId = useRef(0)

  const refresh = useCallback(async () => {
    try {
      const [s, m, p, mp] = await Promise.all([api.schedule(), api.metrics(), api.patients(), api.map()])
      setSchedule(s)
      setReceivedAt(Date.now())
      setMetrics(m)
      setPatients(p)
      setMap(mp)
      setError(null)
    } catch (e) {
      setError(`Can't reach the backend (${e.message}). Is uvicorn running on port 8000?`)
    }
  }, [])

  const log = (text) => {
    const time = new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', second: '2-digit' })
    setActivity((a) => [{ id: nextId.current++, time, text }, ...a].slice(0, 8))
  }

  useEffect(() => {
    refresh()
    return connectSocket(
      '/ws/clinic',
      (msg) => {
        if (msg.summary) log(msg.summary)
        if (msg.type === 'reset') {
          setActivity([])
          setResetKey((k) => k + 1)
        }
        refresh()
      },
      (ok) => {
        setConnected(ok)
        if (ok) refresh()
      },
    )
  }, [refresh])

  const reset = async () => {
    await api.reset()
    setActivity([])
    setResetKey((k) => k + 1)
    refresh()
  }

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>Slot Matcher</h1>
          <div className="muted small">
            Predict no-shows, release slots early, refill them with nearby standby patients.
          </div>
        </div>
        <div className="topbar-right">
          <span className="badge">Synthetic patients (Synthea) · Real MA hospital locations</span>
          <span className={`conn ${connected ? 'on' : 'off'}`} title={connected ? 'Live' : 'Reconnecting'} />
          <button onClick={reset}>Reset demo</button>
        </div>
      </header>
      {error && <div className="error">{error}</div>}
      <MetricsPanel metrics={metrics} />
      <main className="grid">
        <ClinicDashboard
          schedule={schedule}
          receivedAt={receivedAt}
          activity={activity}
          onRelease={async (id, reason) => {
            await api.release(id, reason)
            refresh()
          }}
        />
        <div className="right-col">
          <section className="phones">
            <h2 className="section-title">Standby patients' phones</h2>
            <div className="phone-grid">
              {patients.map((p) => (
                <PatientPhone key={p.id} patientId={p.id} resetKey={resetKey} />
              ))}
            </div>
          </section>
          <MapView map={map} schedule={schedule} />
        </div>
      </main>
    </div>
  )
}
