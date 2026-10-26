import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { toGW } from '../format'

// One bar chart used for all three accuracy views.
// `rows` need a `label`, an `mae` and a `bias` (both MW). `description` is read out by screen readers.
export default function ErrorBars({ rows, description, labelEvery = 1 }) {
  return (
    <div className="chart-box" role="img" aria-label={description}>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid stroke="var(--line)" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fill: 'var(--ink-soft)', fontSize: 11 }}
            tickLine={false}
            interval={labelEvery - 1}
          />
          <YAxis
            tick={{ fill: 'var(--ink-soft)', fontSize: 12 }}
            tickLine={false}
            axisLine={false}
            width={32}
            tickFormatter={(mw) => toGW(mw, 1)}
          />
          <Tooltip content={<BarTooltip />} cursor={{ fill: 'var(--band)' }} />
          <Bar dataKey="mae" fill="var(--bar)" radius={[3, 3, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

function BarTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const row = payload[0].payload
  return (
    <div className="tooltip">
      <strong>{row.label}</strong>
      <div>Typical miss: {toGW(row.mae, 2)} GW</div>
      <div>Bias: {toGW(row.bias, 2)} GW</div>
    </div>
  )
}
