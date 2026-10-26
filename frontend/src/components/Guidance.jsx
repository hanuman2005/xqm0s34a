import { average, formatDayTime, toGW } from '../format'

// Plain-language summary for the buyer: how much wind to count on for the chosen day.
export default function Guidance({ forecast, summary }) {
  const averageForecast = average(forecast.hours.map((hour) => hour.forecast))

  // actual = forecast - error, so these are what the wind is likely to be.
  const expected = averageForecast - summary.bias
  const cautious = averageForecast - summary.error_p90
  const extraCover = averageForecast - cautious

  return (
    <div className="guidance">
      <dl>
        <div>
          <dt>Forecast average</dt>
          <dd>{toGW(averageForecast)} GW</dd>
        </div>
        <div>
          <dt>Expected after bias correction</dt>
          <dd>{toGW(expected)} GW</dd>
        </div>
        <div className="guidance-key">
          <dt>Safe to count on (9 hours in 10)</dt>
          <dd>{toGW(cautious)} GW</dd>
        </div>
      </dl>

      <p className="guidance-note">
        In January, forecasts ran <strong>{toGW(summary.bias)} GW too high</strong> on average. To be covered in 9
        hours out of 10, plan for <strong>{toGW(extraCover)} GW less wind</strong> than the raw forecast.
      </p>

      <p className="guidance-source">
        Forecast created {formatDayTime(forecast.publish_time)}. Order deadline {formatDayTime(forecast.cutoff_utc)}.
      </p>
    </div>
  )
}
