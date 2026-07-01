import { useState, useEffect } from 'react'

/**
 * useLocalStorage
 * ===============
 * Type-safe hook that syncs state with localStorage.
 * Changes in other tabs are automatically reflected via the storage event.
 *
 * @param key          localStorage key
 * @param initialValue fallback when key is absent
 */
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = localStorage.getItem(key)
      return item !== null ? (JSON.parse(item) as T) : initialValue
    } catch {
      return initialValue
    }
  })

  // Write to localStorage whenever value changes
  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(storedValue))
    } catch (err) {
      console.warn(`useLocalStorage: failed to write key "${key}"`, err)
    }
  }, [key, storedValue])

  // Listen for changes in other tabs
  useEffect(() => {
    const handler = (e: StorageEvent) => {
      if (e.key !== key) return
      try {
        if (e.newValue !== null) {
          setStoredValue(JSON.parse(e.newValue) as T)
        }
      } catch {
        // ignore parse errors
      }
    }
    window.addEventListener('storage', handler)
    return () => window.removeEventListener('storage', handler)
  }, [key])

  const setValue = (value: T | ((prev: T) => T)) => {
    setStoredValue((prev) => {
      const next = typeof value === 'function' ? (value as (p: T) => T)(prev) : value
      return next
    })
  }

  const removeValue = () => {
    localStorage.removeItem(key)
    setStoredValue(initialValue)
  }

  return [storedValue, setValue, removeValue] as const
}
