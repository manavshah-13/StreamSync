import { useEffect, useState, useRef } from 'react'

/**
 * Generic cancel-safe data-fetching hook.
 * @param {Function} fetcher – async function that returns data
 * @param {Array}    deps    – dependency array (re-fetches when changed)
 */
export default function useFetch(fetcher, deps = []) {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)
  const abortRef              = useRef(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    fetcher()
      .then((res) => { if (!cancelled) setData(res) })
      .catch((err) => {
        if (!cancelled) setError(err?.response?.data?.message || err.message || 'Request failed')
      })
      .finally(() => { if (!cancelled) setLoading(false) })

    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  const refetch = () => {
    setLoading(true)
    setError(null)
    fetcher()
      .then(setData)
      .catch((err) => setError(err?.response?.data?.message || err.message))
      .finally(() => setLoading(false))
  }

  return { data, loading, error, refetch }
}
