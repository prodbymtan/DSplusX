// Thin wrappers around the FastAPI endpoints. Same origin: Vite proxies /api in dev,
// and FastAPI serves the built app itself in single-process mode.

async function request(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    const err = new Error(body.detail || `Request failed (${res.status})`)
    err.status = res.status
    throw err
  }
  return body
}

export const api = {
  schedule: () => request('/appointments'),
  release: (id, reason) => {
    // "late" reuses the no-show release endpoint (same effect: free the slot and
    // start offering it), it's just surfaced differently in the UI.
    const path = { no_show: 'no-show', cancelled: 'cancel', late: 'no-show' }[reason]
    return request(`/appointments/${id}/${path}`, { method: 'POST' })
  },
  patients: () => request('/patients'),
  patientState: (id) => request(`/patients/${id}/state`),
  setAvailable: (id, isAvailable) =>
    request(`/patients/${id}`, { method: 'PATCH', body: JSON.stringify({ is_available: isAvailable }) }),
  claim: (slotId, patientId) =>
    request(`/slots/${slotId}/claim`, { method: 'POST', body: JSON.stringify({ patient_id: patientId }) }),
  expand: (slotId) => request(`/slots/${slotId}/expand`, { method: 'POST' }),
  metrics: () => request('/metrics'),
  map: () => request('/map'),
  nearestEr: (lat, lon) => request(`/emergency/nearest-er?lat=${lat}&lon=${lon}`),
  reset: () => request('/demo/reset', { method: 'POST' }),
}
