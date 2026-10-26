import { formatDateOnly, formatDayTime, toGW } from '../format'

// Buying advice for the chosen day, built only from errors the buyer already knew at order time.
export default function Guidance({ forecast }) {
  const { history, plan } = forecast

  if (!history) {
    return (
      <p className="guidance-empty">
        Not enough earlier days to estimate forecast errors for this date. Pick a later delivery day (6 Jan or after).
      </p>
    )
  }

  return (
    <div className="guidance">
      <p className="guidance-source">
        Based on the {history.days_used} delivery days up to {formatDateOnly(history.through_date)}. Later days are not
        used, because the buyer could not know them.
      </p>

      <dl>
        <div>
          <dt>Forecast wind (average)</dt>
          <dd>{plan ? toGW(plan.forecast_avg_mw) : '-'} GW</dd>
        </div>
        <div>
          <dt>Past bias (forecast too high by)</dt>
          <dd>{toGW(history.bias)} GW</dd>
        </div>
        <div className="guidance-key">
          <dt>Safe wind to count on</dt>
          <dd>{plan ? toGW(plan.safe_wind_avg_mw) : '-'} GW</dd>
        </div>
      </dl>

      {plan ? <PlanTable plan={plan} /> : <p className="guidance-empty">Enter your demand above to see how much to buy.</p>}

      <p className="guidance-source">
        Forecast created {formatDayTime(forecast.publish_time)}. Order deadline {formatDayTime(forecast.cutoff_utc)}.
      </p>
    </div>
  )
}

// Compares "trust the forecast" with "use the safe wind figure".
function PlanTable({ plan }) {
  const rows = [
    { name: 'Trust the forecast', buy: plan.buy_raw_mw, short: plan.outcome?.shortfall_raw_mwh, extra: plan.outcome?.surplus_raw_mwh },
    { name: 'Use safe wind', buy: plan.buy_guided_mw, short: plan.outcome?.shortfall_guided_mwh, extra: plan.outcome?.surplus_guided_mwh, best: true },
  ]
  const gwh = (mwh) => (mwh == null ? '-' : toGW(mwh, 1))

  return (
    <>
      <table className="plan-table">
        <thead>
          <tr>
            <th scope="col">Plan</th>
            <th scope="col">Buy (GW)</th>
            {plan.outcome && <th scope="col">Came up short (GWh)</th>}
            {plan.outcome && <th scope="col">Bought too much (GWh)</th>}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.name} className={row.best ? 'plan-best' : ''}>
              <th scope="row">{row.name}</th>
              <td>{toGW(row.buy)}</td>
              {plan.outcome && <td>{gwh(row.short)}</td>}
              {plan.outcome && <td>{gwh(row.extra)}</td>}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="guidance-note">
        For {toGW(plan.demand_mw, 0)} GW of demand, buy about <strong>{toGW(plan.buy_guided_mw)} GW</strong> from other
        sources. Short means the wind fell below the plan and power had to be bought late. Too much means money spent
        on power that was not needed.
      </p>
    </>
  )
}
