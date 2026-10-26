// Talks to the Python backend. In production set VITE_API_URL; in development the Vite proxy is used.
const BASE_URL = import.meta.env.VITE_API_URL ?? ''

async function getJson(path, params = {}) {
  const query = new URLSearchParams(params).toString()
  const response = await fetch(`${BASE_URL}${path}${query ? `?${query}` : ''}`)
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed (${response.status})`)
  }
  return response.json()
}

export const fetchConfig = () => getJson('/api/config')
export const fetchForecast = (deliveryDate, cutoff) =>
  getJson('/api/forecast', { delivery_date: deliveryDate, cutoff })
export const fetchAccuracy = (cutoff) => getJson('/api/accuracy', { cutoff })
