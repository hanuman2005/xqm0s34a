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

// demandGW is optional. Without it the backend skips the buy plan.
export const fetchForecast = (deliveryDate, cutoff, demandGW) => {
  const params = { delivery_date: deliveryDate, cutoff }
  if (demandGW !== '' && demandGW != null) params.demand_mw = Number(demandGW) * 1000
  return getJson('/api/forecast', params)
}

export const fetchAccuracy = (cutoff) => getJson('/api/accuracy', { cutoff })
