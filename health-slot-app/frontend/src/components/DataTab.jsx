// Data & impact tab — the hackathon "proof" view: the model + simulation numbers
// and the data sources behind them. Kept separate from the clinic's everyday
// Schedule and Map tabs.

import { pct } from '../hooks'

function Stat({ label, value, sub, feature }) {
  return (
    <div className={`stat ${feature ? 'feature' : ''}`}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  )
}

export default function DataTab({ metrics }) {
  if (!metrics) return <section className="card">Loading data…</section>
  const { model: m, live } = metrics
  const lift = m.available && m.fill_rate_baseline ? (m.fill_rate_ours / m.fill_rate_baseline).toFixed(1) : null
  const ma = m.massachusetts

  return (
    <div>
      <section className="metrics">
        <Stat
          feature
          label="Slots recovered today"
          value={live.slots_recovered}
          sub={`${live.minutes_recovered} clinic minutes · ${live.slots_released} released`}
        />
        {m.available ? (
          <>
            <Stat
              label="No-show slots refilled (sim)"
              value={
                <>
                  {pct(m.fill_rate_baseline)} <span className="arrow">→</span>{' '}
                  <span className="good">{pct(m.fill_rate_ours)}</span>
                </>
              }
              sub={`Random vs model, same 20% outreach · ${lift}×`}
            />
            <Stat
              label="Refills per double-booking"
              value={
                <>
                  {m.refills_per_double_booking.random} <span className="arrow">→</span>{' '}
                  <span className="good">{m.refills_per_double_booking.model}</span>
                </>
              }
              sub="Random vs model targeting"
            />
            <Stat
              label="No-show model"
              value={`AUC ${m.auc}`}
              sub={`Top 20% risk holds ${pct(m.top20_catch_rate)} of no-shows · ${m.n_test.toLocaleString()} test appts`}
            />
            {ma && (
              <Stat
                label="Standby pool within 2 mi (est.)"
                value={
                  <>
                    {ma.boston.standby_within_2mi} <span className="arrow">vs</span> {ma.rural.standby_within_2mi}
                  </>
                }
                sub={`${ma.boston.label} vs ${ma.rural.label} · Synthea MA`}
              />
            )}
          </>
        ) : (
          <Stat label="Model metrics" value="Not found" sub="Run python ml/src/train.py" />
        )}
      </section>

      <section className="card">
        <header className="card-head">
          <h2>How to read these numbers</h2>
        </header>
        <div className="small" style={{ lineHeight: 1.7, color: 'var(--muted)' }}>
          <p><strong style={{ color: 'var(--text)' }}>Slots recovered today</strong> counts slots released during this demo that a standby patient then claimed.</p>
          <p><strong style={{ color: 'var(--text)' }}>No-show slots refilled</strong> is a simulation: targeting the riskiest 20% of appointments with the model refills far more no-show slots than targeting at random, on the same outreach budget.</p>
          <p><strong style={{ color: 'var(--text)' }}>No-show model</strong> is a gradient-boosting model trained on a public Kaggle no-show dataset (110k appointments), tested on later appointments it never saw. AUC 0.735 means it ranks a random no-show above a random show-up about 74% of the time.</p>
          <p><strong style={{ color: 'var(--text)' }}>Standby pool</strong> contrasts a dense urban clinic with a rural one — proximity-based refill works far better where more people live nearby.</p>
          <p>The demo patients themselves are synthetic (Synthea, Massachusetts) and the per-patient inputs are scenario values, so treat the model as the methodology rather than a verdict on any individual. See the project README for the full honesty notes.</p>
        </div>
      </section>
    </div>
  )
}
