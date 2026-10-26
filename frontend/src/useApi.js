import { useEffect, useState } from 'react'

// Runs `load()` whenever `inputs` change and reports { data, loading, error }.
export function useApi(load, inputs) {
  const [state, setState] = useState({ data: null, loading: true, error: null })

  useEffect(() => {
    let cancelled = false // ignore the answer if the inputs changed meanwhile
    setState((previous) => ({ ...previous, loading: true, error: null }))

    load()
      .then((data) => !cancelled && setState({ data, loading: false, error: null }))
      .catch((error) => !cancelled && setState({ data: null, loading: false, error: error.message }))

    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, inputs)

  return state
}
