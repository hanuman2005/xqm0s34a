import { Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { formatTime, toGW } from '../format'

// Hourly forecast (orange) against what really happened (blue), with the usual range of error shaded.
// `history` holds the past errors known at order time (forecast - actual, MW). It is null early in the month.
export default function DayChart({ hours, history }) {
  const rows = hours.map((hour) => ({
    time: formatTime(hour.target_time),
    forecast: hour.forecast,
    actual: hour.actual,
    // If the forecast was too high by error_p90 the actual is forecast - error_p90, and so on.
    range: history ? [hour.forecast - history.error_p90, hour.forecast - history.error_p10] : null,
  }))

  return (
    <div>
      <ul className="legend">
        <li>Gigawatts (GW), hourly, UK time</li>
        <li><span className="swatch" style={{ background: 'var(--series-forecast)' }} />Forecast</li>
        <li><span className="swatch" style={{ background: 'var(--series-actual)' }} />Actual</li>
        {history && <li><span className="swatch swatch-band" />Likely range of actual (80% of past hours)</li>}
      </ul>

      <div className="chart-box" role="img" aria-label="Hourly wind forecast compared with actual generation">
        <ResponsiveContainer width="100%" height={340}>
          <ComposedChart data={rows} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
            <CartesianGrid stroke="var(--line)" vertical={false} />
            <XAxis dataKey="time" tick={{ fill: 'var(--ink-soft)', fontSize: 12 }} tickLine={false} interval={2} />
            <YAxis
              tick={{ fill: 'var(--ink-soft)', fontSize: 12 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(mw) => toGW(mw, 0)}
              width={28}
              domain={[0, 'auto']}
            />
            <Tooltip content={<DayTooltip />} />
            <Area dataKey="range" fill="var(--band)" stroke="none" isAnimationActive={false} />
            <Line dataKey="forecast" stroke="var(--series-forecast)" strokeWidth={2} dot={false} isAnimationActive={false} />
            <Line dataKey="actual" stroke="var(--series-actual)" strokeWidth={2} dot={false} isAnimationActive={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

function DayTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const row = payload[0].payload
  return (
    <div className="tooltip">
      <strong>{label}</strong>
      <div>Forecast: {toGW(row.forecast, 2)} GW</div>
      {row.actual != null && <div>Actual: {toGW(row.actual, 2)} GW</div>}
      {row.range && <div>Likely range: {toGW(row.range[0], 1)} to {toGW(row.range[1], 1)} GW</div>}
    </div>
  )
}
