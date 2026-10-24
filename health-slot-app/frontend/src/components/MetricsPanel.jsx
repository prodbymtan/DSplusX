import { pct } from '../hooks'

function Stat({ label, value, sub }) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  )
}

export default function MetricsPanel({ metrics }) {
  if (!metrics) return null
  const { model: m, live } = metrics
  const lift = m.available && m.fill_rate_baseline ? (m.fill_rate_ours / m.fill_rate_baseline).toFixed(1) : null
  const ma = m.massachusetts

  return (
    <section className="metrics">
      <Stat
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
                {pct(m.fill_rate_baseline)} <span className="arrow">→</span> <span className="good">{pct(m.fill_rate_ours)}</span>
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
              sub={`${ma.boston.label} vs ${ma.rural.label} · Synthea MA population`}
            />
          )}
        </>
      ) : (
        <Stat label="Model metrics" value="Not found" sub="Run python ml/src/train.py" />
      )}
    </section>
  )
}
