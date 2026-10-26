import { useState } from 'react'
import './App.css'
import { fetchAccuracy, fetchConfig, fetchForecast } from './api'
import AccuracySection from './components/AccuracySection'
import Card from './components/Card'
import Controls from './components/Controls'
import DayChart from './components/DayChart'
import Guidance from './components/Guidance'
import OrderTable from './components/OrderTable'
import { formatDateOnly, formatDayTime } from './format'
import { useApi } from './useApi'

export default function App() {
  const config = useApi(fetchConfig, [])

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-inner">
          <h1>Wind Forecast Monitor</h1>
          <p>Day-ahead wind generation for the GB market. Source: Elexon BMRS.</p>
        </div>
      </header>

      <main className="app-main">
        {config.error && <p className="card-message card-error">{config.error}</p>}
        {config.data && <Dashboard config={config.data} />}
        {config.loading && !config.data && <p className="card-message">Loading…</p>}
      </main>

      <footer className="app-footer">
        Accuracy is measured on the forecast published before the order deadline, so it only uses information the
        buyer had at the time. Error = forecast minus actual. Hourly actuals are the average of two half-hour readings.
      </footer>
    </div>
  )
}

function Dashboard({ config }) {
  const [deliveryDate, setDeliveryDate] = useState(config.last_delivery_date) // latest day: it has the most history
  const [cutoff, setCutoff] = useState(config.default_cutoff)

  const [demandGW, setDemandGW] = useState('30')

  const forecast = useApi(() => fetchForecast(deliveryDate, cutoff, demandGW), [deliveryDate, cutoff, demandGW])
  const accuracy = useApi(() => fetchAccuracy(cutoff), [cutoff])

  return (
    <>
      <Controls
        config={config}
        deliveryDate={deliveryDate}
        onDeliveryDateChange={setDeliveryDate}
        cutoff={cutoff}
        onCutoffChange={setCutoff}
        demandGW={demandGW}
        onDemandChange={setDemandGW}
      />

      <div className="grid-day">
        <Card
          title={`Wind forecast for ${formatDateOnly(deliveryDate)}`}
          subtitle={forecast.data && `Latest forecast available at the order deadline (created ${formatDayTime(forecast.data.publish_time)})`}
          state={forecast}
        >
          {forecast.data && <DayChart hours={forecast.data.hours} history={forecast.data.history} />}
        </Card>

        <Card title="How much to buy" subtitle="Wind to count on, and the amount to buy" state={forecast}>
          {forecast.data && <Guidance forecast={forecast.data} />}
        </Card>
      </div>

      {forecast.data?.order && (
        <Card title="Recommended order" subtitle="Power to buy from other sources in each hour, using the safe wind figure">
          <OrderTable forecast={forecast.data} />
        </Card>
      )}

      <AccuracySection accuracy={accuracy} />
    </>
  )
}
