import { formatDateOnly } from '../format'

// Day and decision-time pickers. Changing either one reloads every number on the page.
export default function Controls({ config, deliveryDate, onDeliveryDateChange, cutoff, onCutoffChange }) {
  const first = config.first_delivery_date
  const last = config.last_delivery_date

  // Move the date by +1 or -1 day (noon avoids any time-zone edge case).
  const shiftDay = (days) => {
    const date = new Date(`${deliveryDate}T12:00:00Z`)
    date.setUTCDate(date.getUTCDate() + days)
    onDeliveryDateChange(date.toISOString().slice(0, 10))
  }

  return (
    <div className="controls">
      <div className="control">
        <span className="control-label">Delivery day</span>
        <div className="day-picker">
          <button type="button" aria-label="Previous day" disabled={deliveryDate <= first} onClick={() => shiftDay(-1)}>
            ‹
          </button>
          <input
            type="date"
            aria-label="Delivery day"
            value={deliveryDate}
            min={first}
            max={last}
            onChange={(event) => event.target.value && onDeliveryDateChange(event.target.value)}
          />
          <button type="button" aria-label="Next day" disabled={deliveryDate >= last} onClick={() => shiftDay(1)}>
            ›
          </button>
        </div>
      </div>

      <div className="control">
        <span className="control-label">Order placed by (day before, UK time)</span>
        <input
          type="time"
          aria-label="Order cutoff time"
          value={cutoff}
          onChange={(event) => event.target.value && onCutoffChange(event.target.value)}
        />
      </div>

      <p className="controls-summary">
        Showing <strong>{formatDateOnly(deliveryDate)}</strong> with the forecast available at{' '}
        <strong>{cutoff}</strong> the day before.
      </p>
    </div>
  )
}
