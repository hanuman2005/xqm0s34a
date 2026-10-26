import { toGW } from '../format'

// Four headline accuracy numbers for the whole of January.
export default function KpiRow({ summary }) {
  const tiles = [
    {
      label: 'Typical miss (MAE)',
      value: `${toGW(summary.mae)} GW`,
      help: `${((summary.mae / summary.mean_actual) * 100).toFixed(0)}% of average wind output`,
    },
    {
      label: 'Forecast bias',
      value: `+${toGW(summary.bias)} GW`,
      help: 'Forecast was too high on average',
      warn: summary.bias > 0,
    },
    {
      label: 'Big misses (RMSE)',
      value: `${toGW(summary.rmse)} GW`,
      help: 'Like MAE, but counts large errors more',
    },
    {
      label: 'Worst 1 hour in 10',
      value: `${toGW(summary.error_p90)} GW`,
      help: 'Forecast too high by at least this much',
    },
  ]

  return (
    <ul className="kpi-row">
      {tiles.map((tile) => (
        <li key={tile.label} className={`kpi ${tile.warn ? 'kpi-warn' : ''}`}>
          <span className="kpi-label">{tile.label}</span>
          <span className="kpi-value">{tile.value}</span>
          <span className="kpi-help">{tile.help}</span>
        </li>
      ))}
    </ul>
  )
}
