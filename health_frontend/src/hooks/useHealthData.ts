/**
 * useHealthData
 * =============
 * Shared hook that fetches health logs + recommendation insights
 * and exposes them to any page component.
 *
 * Provides:
 *   todayLog       — today's HealthLog or null
 *   recentLogs     — last N health logs
 *   insights       — latest HealthInsightsResponse or null
 *   loading        — global loading flag
 *   insightsLoading— ML engine loading flag
 *   error          — error message or null
 *   refresh        — re-fetch everything
 *   generateInsights(metrics) — trigger recommendation engine
 */

import { useState, useCallback } from 'react'
import { healthApi, recommendationApi } from '../api/health'
import type { HealthLog, HealthInsightsResponse, HealthMetrics } from '../types'
import { getApiError } from '../utils'

interface UseHealthDataOptions {
  autoFetch?:     boolean
  logLimit?:      number
  autoInsights?:  boolean
}

export function useHealthData({
  autoFetch    = true,
  logLimit     = 14,
  autoInsights = false,
}: UseHealthDataOptions = {}) {
  const [todayLog,        setTodayLog]        = useState<HealthLog | null>(null)
  const [recentLogs,      setRecentLogs]      = useState<HealthLog[]>([])
  const [insights,        setInsights]        = useState<HealthInsightsResponse | null>(null)
  const [loading,         setLoading]         = useState(false)
  const [insightsLoading, setInsightsLoading] = useState(false)
  const [error,           setError]           = useState<string | null>(null)

  const fetchLogs = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [tLog, logs] = await Promise.all([
        healthApi.getTodayLog(),
        healthApi.listLogs({ limit: logLimit }),
      ])
      setTodayLog(tLog)
      setRecentLogs(logs)

      // Optionally auto-generate insights from today's log
      if (autoInsights && tLog) {
        await generateInsights({
          sleep_hours:     (tLog as any).sleep_hours     ?? undefined,
          steps:           (tLog as any).steps           ?? undefined,
          calories:        (tLog as any).calories        ?? undefined,
          water_intake_ml: (tLog as any).water_intake_ml ?? undefined,
          stress_level:    tLog.stress_level             ?? undefined,
          heart_rate_bpm:  (tLog as any).heart_rate_bpm  ?? undefined,
        })
      }
    } catch (err) {
      setError(getApiError(err))
    } finally {
      setLoading(false)
    }
  }, [logLimit, autoInsights])

  const generateInsights = useCallback(async (metrics: HealthMetrics) => {
    setInsightsLoading(true)
    setError(null)
    try {
      const result = await recommendationApi.generate(metrics)
      setInsights(result)
      return result
    } catch (err) {
      setError(getApiError(err))
      return null
    } finally {
      setInsightsLoading(false)
    }
  }, [])

  const refresh = useCallback(() => fetchLogs(), [fetchLogs])

  // Note: Callers are responsible for calling refresh() / fetchLogs()
  // in their own useEffect — this avoids double-fetch in React StrictMode.

  return {
    todayLog,
    recentLogs,
    insights,
    loading,
    insightsLoading,
    error,
    refresh,
    fetchLogs,
    generateInsights,
    setInsights,
    setError,
  }
}
