import { useState, useEffect } from 'react'

/**
 * Debounces a value by the given delay (ms).
 * Useful for search inputs to avoid hammering the API on every keystroke.
 */
export default function useDebounce(value, delay = 350) {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])

  return debounced
}
