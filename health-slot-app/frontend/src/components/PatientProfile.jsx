// Patient profile panel: personal info, wearable readings, and file uploads.
//
// Demo-only persistence: the backend Patient model has no columns for health
// history, wearable metrics, or documents, so this is stored in localStorage
// rather than invent a schema + migration for the hackathon. Everything stays
// on the patient's own device. Keyed per patient so multiple demo patients
// don't clash.

import { useEffect, useMemo, useRef, useState } from 'react'

const key = (patientId) => `patient_profile_v1_${patientId}`

const EMPTY = {
  // Personal
  fullName: '',
  dob: '',
  phone: '',
  insurance: '',
  conditions: '',
  medications: '',
  allergies: '',
  // Wearable
  restingHr: '',
  steps: '',
  sleepHours: '',
  spo2: '',
  hrv: '',
  device: '',
  // Uploaded documents: { id, name, size, type, dataUrl? }
  files: [],
}

// Keep localStorage small: only inline files under this size as data URLs.
const INLINE_LIMIT = 1_500_000 // ~1.5 MB

function load(patientId) {
  try {
    const raw = localStorage.getItem(key(patientId))
    return raw ? { ...EMPTY, ...JSON.parse(raw) } : EMPTY
  } catch {
    return EMPTY
  }
}

function fmtSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

const readAsDataUrl = (file) =>
  new Promise((resolve, reject) => {
    const r = new FileReader()
    r.onload = () => resolve(r.result)
    r.onerror = reject
    r.readAsDataURL(file)
  })

export default function PatientProfile({ patientId, onClose }) {
  const [form, setForm] = useState(() => load(patientId))
  const [saved, setSaved] = useState(false)
  const [dragging, setDragging] = useState(false)
  const fileInput = useRef(null)

  useEffect(() => {
    setForm(load(patientId))
  }, [patientId])

  useEffect(() => {
    if (saved) {
      const t = setTimeout(() => setSaved(false), 2500)
      return () => clearTimeout(t)
    }
  }, [saved])

  const set = (name) => (e) => {
    setForm((f) => ({ ...f, [name]: e.target.value }))
    setSaved(false)
  }

  const addFiles = async (fileList) => {
    const incoming = Array.from(fileList || [])
    if (!incoming.length) return
    const prepared = await Promise.all(
      incoming.map(async (file) => ({
        id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
        name: file.name,
        size: file.size,
        type: file.type || 'file',
        dataUrl: file.size <= INLINE_LIMIT ? await readAsDataUrl(file) : null,
      })),
    )
    setForm((f) => ({ ...f, files: [...f.files, ...prepared] }))
    setSaved(false)
  }

  const removeFile = (id) => {
    setForm((f) => ({ ...f, files: f.files.filter((x) => x.id !== id) }))
    setSaved(false)
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    addFiles(e.dataTransfer.files)
  }

  const save = (e) => {
    e.preventDefault()
    try {
      localStorage.setItem(key(patientId), JSON.stringify(form))
      setSaved(true)
    } catch {
      /* storage full or unavailable (e.g. a big file in private mode) */
      setSaved(false)
    }
  }

  const clearAll = () => {
    setForm(EMPTY)
    try {
      localStorage.removeItem(key(patientId))
    } catch {
      /* ignore */
    }
    setSaved(false)
  }

  const fileCount = form.files.length
  const totalSize = useMemo(() => form.files.reduce((n, f) => n + f.size, 0), [form.files])

  return (
    <div className="profile-overlay" role="dialog" aria-modal="true" aria-label="Patient profile">
      <div className="profile-sheet">
        <div className="profile-head">
          <div>
            <h2>Your profile</h2>
            <div className="muted small">Personal details, wearable data, and documents. Saved on this device.</div>
          </div>
          <button className="ghost" onClick={onClose} aria-label="Close profile">Close</button>
        </div>

        <form className="profile-form" onSubmit={save}>
          <h3>Personal information</h3>
          <div className="profile-grid">
            <label className="field">
              <span>Full name</span>
              <input value={form.fullName} onChange={set('fullName')} placeholder="Glenn A." />
            </label>
            <label className="field">
              <span>Date of birth</span>
              <input type="date" value={form.dob} onChange={set('dob')} />
            </label>
            <label className="field">
              <span>Phone</span>
              <input type="tel" value={form.phone} onChange={set('phone')} placeholder="(617) 555-0142" />
            </label>
            <label className="field">
              <span>Insurance</span>
              <input value={form.insurance} onChange={set('insurance')} placeholder="BCBS, Tufts, MassHealth…" />
            </label>
            <label className="field wide">
              <span>Existing conditions</span>
              <input value={form.conditions} onChange={set('conditions')} placeholder="e.g. hypertension, diabetes" />
            </label>
            <label className="field wide">
              <span>Current medications</span>
              <input value={form.medications} onChange={set('medications')} placeholder="e.g. metformin, lisinopril" />
            </label>
            <label className="field wide">
              <span>Allergies</span>
              <input value={form.allergies} onChange={set('allergies')} placeholder="e.g. penicillin" />
            </label>
          </div>

          <h3>Wearable data</h3>
          <div className="profile-grid">
            <label className="field">
              <span>Resting heart rate (bpm)</span>
              <input type="number" min="20" max="220" value={form.restingHr} onChange={set('restingHr')} placeholder="62" />
            </label>
            <label className="field">
              <span>Steps today</span>
              <input type="number" min="0" value={form.steps} onChange={set('steps')} placeholder="8200" />
            </label>
            <label className="field">
              <span>Sleep last night (hrs)</span>
              <input type="number" min="0" max="24" step="0.1" value={form.sleepHours} onChange={set('sleepHours')} placeholder="7.5" />
            </label>
            <label className="field">
              <span>Blood oxygen SpO₂ (%)</span>
              <input type="number" min="50" max="100" value={form.spo2} onChange={set('spo2')} placeholder="98" />
            </label>
            <label className="field">
              <span>Heart rate variability (ms)</span>
              <input type="number" min="0" max="300" value={form.hrv} onChange={set('hrv')} placeholder="45" />
            </label>
            <label className="field">
              <span>Device</span>
              <select value={form.device} onChange={set('device')}>
                <option value="">Select…</option>
                <option value="apple_watch">Apple Watch</option>
                <option value="fitbit">Fitbit</option>
                <option value="garmin">Garmin</option>
                <option value="oura">Oura Ring</option>
                <option value="other">Other</option>
              </select>
            </label>
          </div>

          <h3>Documents</h3>
          <div
            className={`dropzone ${dragging ? 'dragging' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => fileInput.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') fileInput.current?.click() }}
            aria-label="Upload documents: click to choose files or drop them here"
          >
            <div className="dz-icon" aria-hidden="true">⬆</div>
            <div>Drop files here or <span className="link">browse</span></div>
            <div className="muted small">Lab results, referrals, insurance card, prior records</div>
            <input
              ref={fileInput}
              type="file"
              multiple
              hidden
              onChange={(e) => { addFiles(e.target.files); e.target.value = '' }}
            />
          </div>

          {fileCount > 0 && (
            <ul className="file-list">
              {form.files.map((f) => (
                <li key={f.id} className="file-row">
                  <span className="file-ico" aria-hidden="true">📄</span>
                  <span className="file-name">
                    {f.dataUrl ? (
                      <a href={f.dataUrl} download={f.name}>{f.name}</a>
                    ) : (
                      f.name
                    )}
                  </span>
                  <span className="file-size muted small">{fmtSize(f.size)}</span>
                  <button
                    type="button"
                    className="ghost file-remove"
                    onClick={() => removeFile(f.id)}
                    aria-label={`Remove ${f.name}`}
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}
          {fileCount > 0 && (
            <div className="muted small">
              {fileCount} file{fileCount > 1 ? 's' : ''} · {fmtSize(totalSize)} total
            </div>
          )}

          <div className="profile-actions">
            <button type="submit" className="primary">Save profile</button>
            <button type="button" className="ghost" onClick={clearAll}>Clear all</button>
            {saved && <span className="ok small" role="status">Saved on this device</span>}
          </div>
          <div className="muted small profile-note">
            Demo only. Everything here is stored locally in your browser and never uploaded to a server.
          </div>
        </form>
      </div>
    </div>
  )
}
