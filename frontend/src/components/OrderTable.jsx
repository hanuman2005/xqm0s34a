import { formatDateOnly, formatDayTime, formatTime, toGW } from '../format'

// Hour-by-hour order the buyer can place, plus a one-sentence summary and a CSV download.
export default function OrderTable({ forecast }) {
  const { order, plan } = forecast
  if (!order) return null

  const totalMWh = order.reduce((sum, hour) => sum + hour.buy_mw, 0)
  const peak = order.reduce((max, hour) => (hour.buy_mw > max.buy_mw ? hour : max), order[0])

  return (
    <div>
      <p className="order-summary">
        Order <strong>{toGW(totalMWh, 0)} GWh</strong> for {formatDateOnly(forecast.delivery_date)} before{' '}
        <strong>{formatDayTime(forecast.cutoff_utc)}</strong>. That is {toGW(plan.buy_guided_mw)} GW on average, with the
        most needed at <strong>{formatTime(peak.target_time)}</strong> ({toGW(peak.buy_mw)} GW).
      </p>

      <div className="order-scroll">
        <table className="order-table">
          <thead>
            <tr>
              <th scope="col">Hour</th>
              <th scope="col">Forecast wind (GW)</th>
              <th scope="col">Safe wind (GW)</th>
              <th scope="col">Order (GW)</th>
            </tr>
          </thead>
          <tbody>
            {order.map((hour) => (
              <tr key={hour.target_time}>
                <th scope="row">{formatTime(hour.target_time)}</th>
                <td>{toGW(hour.forecast_mw, 2)}</td>
                <td>{toGW(hour.safe_wind_mw, 2)}</td>
                <td><strong>{toGW(hour.buy_mw, 2)}</strong></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <button type="button" className="download" onClick={() => downloadCsv(forecast)}>
        Download order as CSV
      </button>
    </div>
  )
}

// Builds a small CSV file in the browser and saves it.
function downloadCsv(forecast) {
  const lines = ['hour_uk,forecast_wind_mw,safe_wind_mw,order_mw']
  forecast.order.forEach((hour) =>
    lines.push([formatTime(hour.target_time), hour.forecast_mw, hour.safe_wind_mw, hour.buy_mw].map((v) => (typeof v === 'number' ? Math.round(v) : v)).join(','))
  )

  const link = document.createElement('a')
  link.href = URL.createObjectURL(new Blob([lines.join('\n')], { type: 'text/csv' }))
  link.download = `order-${forecast.delivery_date}.csv`
  link.click()
  URL.revokeObjectURL(link.href)
}
