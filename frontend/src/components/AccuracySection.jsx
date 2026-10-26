import { formatDateOnly } from '../format'
import Card from './Card'
import ErrorBars from './ErrorBars'
import KpiRow from './KpiRow'

// "How good are the forecasts?" - headline numbers plus three breakdowns.
export default function AccuracySection({ accuracy }) {
  const { data } = accuracy

  return (
    <section aria-labelledby="accuracy-heading">
      <h2 id="accuracy-heading" className="section-title">
        How accurate were the forecasts in January 2026?
      </h2>

      {data && <KpiRow summary={data.summary} />}

      <div className="grid-3">
        <Card title="By day" subtitle="Typical miss for each delivery day (GW)" state={accuracy}>
          {data && (
            <ErrorBars
              description="Typical forecast error for each delivery day"
              labelEvery={5}
              rows={data.by_delivery_day.map((row) => ({
                ...row,
                label: formatDateOnly(row.delivery_date).replace(/^\w+ /, ''),
              }))}
            />
          )}
        </Card>

        <Card title="By hour of day" subtitle="Typical miss at each hour, UK time (GW)" state={accuracy}>
          {data && (
            <ErrorBars
              description="Typical forecast error for each hour of the day"
              labelEvery={3}
              rows={data.by_hour_of_day.map((row) => ({ ...row, label: `${String(row.hour).padStart(2, '0')}:00` }))}
            />
          )}
        </Card>

        <Card title="By how far ahead" subtitle="Typical miss by hours between forecast and delivery (GW)" state={accuracy}>
          {data && (
            <ErrorBars
              description="Typical forecast error by hours between forecast creation and delivery"
              labelEvery={2}
              rows={data.by_lead_time
                .filter((row) => row.bucket_end <= 72)
                .map((row) => ({ ...row, label: `${row.bucket_start}-${row.bucket_end}` }))}
            />
          )}
        </Card>
      </div>
    </section>
  )
}
