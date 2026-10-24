import { useId, useState } from 'react'

// Relay login.
//
// Auth status: the backend (health-slot-app/backend) currently exposes NO login/auth
// endpoint — there is no /api/login, /api/auth, session, or token route. So this screen
// does not fake a sign-in. The email/password form is validated client-side, and the only
// real way through is the clearly labelled "Continue to demo" button.
//
// TODO(auth): when the backend gains a real auth endpoint, wire it up here, e.g.
//   import { api } from '../services/api'
//   const res = await api.login({ email, password, role })   // role: 'patient' | 'staff'
//   onAuthenticated(res)
// Then replace the "not available yet" message below with the real request + error handling,
// and gate the demo button behind an explicit demo flag.

export default function LoginScreen({ onContinue }) {
  const [role, setRole] = useState('patient') // 'patient' | 'staff'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [errors, setErrors] = useState({}) // { email?, password?, form? }
  const [submitting, setSubmitting] = useState(false)

  const emailId = useId()
  const pwId = useId()
  const emailErrId = useId()
  const pwErrId = useId()

  const validate = () => {
    const next = {}
    if (!email.trim()) next.email = 'Enter your email address.'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) next.email = 'Enter a valid email address.'
    if (!password) next.password = 'Enter your password.'
    return next
  }

  const onSubmit = async (e) => {
    e.preventDefault()
    const next = validate()
    if (Object.keys(next).length) {
      setErrors(next)
      return
    }
    setErrors({})
    setSubmitting(true)
    // No auth endpoint exists yet (see TODO above). Be honest instead of faking a session.
    setTimeout(() => {
      setSubmitting(false)
      setErrors({ form: 'Sign-in isn’t connected yet. Use “Continue to demo” to explore the dashboard.' })
    }, 150)
  }

  return (
    <main className="login">
      <div className="login-card">
        <h1 className="login-brand">
          <span className="login-mark" aria-hidden="true" />
          Relay
        </h1>
        <p className="login-tagline">Your health data and your care, passed along.</p>

        <div className="seg" role="group" aria-label="Who are you signing in as?">
          <button type="button" aria-pressed={role === 'patient'} onClick={() => setRole('patient')}>
            Patient
          </button>
          <button type="button" aria-pressed={role === 'staff'} onClick={() => setRole('staff')}>
            Clinic staff
          </button>
        </div>

        <form onSubmit={onSubmit} noValidate>
          {errors.form && (
            <div className="form-error" role="alert">
              {errors.form}
            </div>
          )}

          <div className="field">
            <label htmlFor={emailId}>Email</label>
            <input
              id={emailId}
              type="email"
              inputMode="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              aria-invalid={errors.email ? 'true' : undefined}
              aria-describedby={errors.email ? emailErrId : undefined}
              placeholder="you@example.com"
            />
            {errors.email && (
              <p className="field-error" id={emailErrId}>
                {errors.email}
              </p>
            )}
          </div>

          <div className="field">
            <label htmlFor={pwId}>Password</label>
            <div className="pw-wrap">
              <input
                id={pwId}
                type={showPw ? 'text' : 'password'}
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                aria-invalid={errors.password ? 'true' : undefined}
                aria-describedby={errors.password ? pwErrId : undefined}
                placeholder="Your password"
              />
              <button
                type="button"
                className="pw-toggle"
                onClick={() => setShowPw((v) => !v)}
                aria-pressed={showPw}
                aria-label={showPw ? 'Hide password' : 'Show password'}
              >
                {showPw ? 'Hide' : 'Show'}
              </button>
            </div>
            {errors.password && (
              <p className="field-error" id={pwErrId}>
                {errors.password}
              </p>
            )}
          </div>

          <button type="submit" className="btn-primary" disabled={submitting}>
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <div className="login-divider">or</div>

        <button type="button" className="btn-demo" onClick={onContinue}>
          Continue to demo
        </button>
        <p className="login-demo-note">No account needed. Opens the live dashboard with demo data.</p>
      </div>
    </main>
  )
}
