import { create } from 'zustand'
import type { HealthLog, HealthInsightsResponse } from '../types'

interface HealthState {
  // Today's log
  todayLog:   HealthLog | null
  setTodayLog: (log: HealthLog | null) => void

  // Recent logs (last N days)
  recentLogs:     HealthLog[]
  setRecentLogs:  (logs: HealthLog[]) => void
  prependLog:     (log: HealthLog) => void
  updateLog:      (id: string, updated: HealthLog) => void
  removeLog:      (id: string) => void

  // Latest recommendation insights
  insights:     HealthInsightsResponse | null
  setInsights:  (ins: HealthInsightsResponse | null) => void

  // Loading states
  logsLoading:     boolean
  insightsLoading: boolean
  setLogsLoading:     (v: boolean) => void
  setInsightsLoading: (v: boolean) => void

  // Reset (on logout)
  reset: () => void
}

const INITIAL: Pick<
  HealthState,
  'todayLog' | 'recentLogs' | 'insights' | 'logsLoading' | 'insightsLoading'
> = {
  todayLog:        null,
  recentLogs:      [],
  insights:        null,
  logsLoading:     false,
  insightsLoading: false,
}

export const useHealthStore = create<HealthState>((set) => ({
  ...INITIAL,

  setTodayLog:  (log)  => set({ todayLog: log }),

  setRecentLogs: (logs) => set({ recentLogs: logs }),

  prependLog: (log) =>
    set((state) => ({
      recentLogs: [log, ...state.recentLogs.filter((l) => l.id !== log.id)],
    })),

  updateLog: (id, updated) =>
    set((state) => ({
      recentLogs: state.recentLogs.map((l) => (l.id === id ? updated : l)),
      todayLog:   state.todayLog?.id === id ? updated : state.todayLog,
    })),

  removeLog: (id) =>
    set((state) => ({
      recentLogs: state.recentLogs.filter((l) => l.id !== id),
      todayLog:   state.todayLog?.id === id ? null : state.todayLog,
    })),

  setInsights:        (ins) => set({ insights: ins }),
  setLogsLoading:     (v)   => set({ logsLoading: v }),
  setInsightsLoading: (v)   => set({ insightsLoading: v }),

  reset: () => set(INITIAL),
}))
