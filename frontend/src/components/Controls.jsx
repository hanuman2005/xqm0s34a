import { formatDateOnly } from '../format'

// Day and decision-time pickers. Changing either one reloads every number on the page.
export default function Controls({
  config,
  deliveryDate,
  onDeliveryDateChange,
  cutoff,
  onCutoffChange,
  demandGW,
  onDemandChange,
}) {
  const first = config.first_delivery_date
  const last = config.last_delivery_date

  // Add or subtract days from a "YYYY-MM-DD" date (noon avoids any time-zone edge case).
  const addDays = (isoDate, days) => {
    const date = new Date(`${isoDate}T12:00:00Z`)
    date.setUTCDate(date.getUTCDate() + days)
    return date.toISOString().slice(0, 10)
  }
  const shiftDay = (days) => onDeliveryDateChange(addDays(deliveryDate, days))

  // Orders are placed the day before delivery.
  const orderDay = addDays(deliveryDate, -1)

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
        <span className="control-label">Order deadline (UK time)</span>
        <div className="day-picker">
          <span className="fixed-date" title="The order is placed the day before delivery">
            {formatDateOnly(orderDay)}
          </span>
          <input
            type="time"
            aria-label="Order cutoff time"
            value={cutoff}
            onChange={(event) => event.target.value && onCutoffChange(event.target.value)}
          />
        </div>
      </div>

      <div className="control">
        <span className="control-label">Your demand that day (GW, same every hour)</span>
        <input
          type="number"
          aria-label="Demand in gigawatts"
          min="0"
          step="0.5"
          value={demandGW}
          onChange={(event) => onDemandChange(event.target.value)}
        />
      </div>

      <p className="controls-summary">
        Order on <strong>{formatDateOnly(orderDay)}</strong> by <strong>{cutoff}</strong>, for delivery on{' '}
        <strong>{formatDateOnly(deliveryDate)}</strong>. The forecast shown is the latest one available at that deadline.
      </p>
    </div>
  )
}
