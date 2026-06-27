import { useState, useEffect } from 'react'

/**
 * useDebounce
 * ===========
 * Returns a debounced version of the value that only updates
 * after `delay` milliseconds have passed since the last change.
 *
 * Typical use: debounce search inputs before firing API calls.
 *
 * @example
 * const debouncedQuery = useDebounce(searchQuery, 400)
 * useEffect(() => { fetchResults(debouncedQuery) }, [debouncedQuery])
 */
export function useDebounce<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState<T>(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])

  return debounced
}
