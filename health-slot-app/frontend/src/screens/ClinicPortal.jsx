// The clinic console. Two tabs:
//   Schedule — today's appointments, release a slot, watch it auto-refill.
//   Data     — model + simulation numbers and the map (hackathon "proof" tab;
//              the clinic doesn't need this day to day).
//
// All data comes from the existing FastAPI endpoints; nothing here changes the backend.

import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../services/api'
import { connectSocket } from '../services/socket'
import ClinicSchedule from '../components/ClinicSchedule'
import ClinicMap from '../components/ClinicMap'
import DataTab from '../components/DataTab'

export default function ClinicPortal() {
  const [tab, setTab] = useState('schedule')
  const [schedule, setSchedule] = useState(null)
  const [receivedAt, setReceivedAt] = useState(Date.now())
  const [metrics, setMetrics] = useState(null)
  const [patients, setPatients] = useState([])
  const [map, setMap] = useState(null)
  const [activity, setActivity] = useState([])
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState(null)
  const [lastBooked, setLastBooked] = useState(null)
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
        if (msg.type === 'slot_booked') {
          setLastBooked({ id: nextId.current++, text: msg.summary })
          setTimeout(() => setLastBooked(null), 8000)
        }
        if (msg.type === 'reset') setActivity([])
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
    setLastBooked(null)
    refresh()
  }

  return (
    <div className="shell">
      <div className="appbar">
        <div className="brand">
          <span className="mark">🏥</span>
          <span>
            <div className="title">Slot Matcher · Clinic</div>
            <div className="subtitle">{schedule?.clinic?.name || 'Loading…'}</div>
          </span>
        </div>
        <div className="appbar-right">
          <span className="conn-label">
            <span className={`conn ${connected ? 'on' : 'off'}`} /> {connected ? 'Live' : 'Reconnecting'}
          </span>
          <button onClick={reset}>Reset demo</button>
        </div>
      </div>

      <div className="content">
        <div className="tabs" role="tablist">
          <button className={`tab ${tab === 'schedule' ? 'active' : ''}`} onClick={() => setTab('schedule')}>
            Schedule
          </button>
          <button className={`tab ${tab === 'map' ? 'active' : ''}`} onClick={() => setTab('map')}>
            Map
          </button>
          <button className={`tab ${tab === 'data' ? 'active' : ''}`} onClick={() => setTab('data')}>
            Data &amp; impact
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        {tab === 'schedule' && (
          <ClinicSchedule
            schedule={schedule}
            patients={patients}
            receivedAt={receivedAt}
            activity={activity}
            lastBooked={lastBooked}
            onRelease={async (id, reason) => {
              await api.release(id, reason)
              refresh()
            }}
          />
        )}
        {tab === 'map' && (
          <ClinicMap
            map={map}
            schedule={schedule}
            receivedAt={receivedAt}
            onExpand={async (slotId) => {
              await api.expand(slotId)
              refresh()
            }}
          />
        )}
        {tab === 'data' && <DataTab metrics={metrics} />}
      </div>
    </div>
  )
}
