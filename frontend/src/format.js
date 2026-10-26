// Small helpers that turn raw numbers and timestamps into text for people.

const LONDON = 'Europe/London'

export const toGW = (megawatts, digits = 1) => (megawatts / 1000).toFixed(digits)

export const signedGW = (megawatts, digits = 1) => `${megawatts > 0 ? '+' : ''}${toGW(megawatts, digits)}`

export const formatTime = (iso) =>
  new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: LONDON })

export const formatDay = (iso) =>
  new Date(iso).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', timeZone: LONDON })

export const formatDayTime = (iso) => `${formatDay(iso)}, ${formatTime(iso)}`

// "2026-01-15" -> "Thu 15 Jan"
export const formatDateOnly = (isoDate) => formatDay(`${isoDate}T12:00:00Z`)

export const average = (numbers) => numbers.reduce((sum, n) => sum + n, 0) / numbers.length
