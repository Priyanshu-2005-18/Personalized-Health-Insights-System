import apiClient from './client'
import type {
  HealthInsightsResponse,
  HealthLog,
  HealthLogCreate,
  HealthMetrics,
  SleepLog,
  ActivityLog,
  PaginatedResponse,
} from '../types'

// ── Daily health logs ─────────────────────────────────────────
export const healthApi = {
  createLog: async (data: HealthLogCreate): Promise<HealthLog> => {
    const res = await apiClient.post<HealthLog>('/health/logs', data)
    return res.data
  },

  listLogs: async (params?: {
    start_date?: string
    end_date?: string
    limit?: number
    offset?: number
  }): Promise<HealthLog[]> => {
    const res = await apiClient.get<HealthLog[]>('/health/logs', { params })
    return res.data
  },

  getTodayLog: async (): Promise<HealthLog | null> => {
    try {
      const res = await apiClient.get<HealthLog>('/health/logs/today')
      return res.data
    } catch {
      return null
    }
  },

  updateLog: async (id: string, data: Partial<HealthLogCreate>): Promise<HealthLog> => {
    const res = await apiClient.patch<HealthLog>(`/health/logs/${id}`, data)
    return res.data
  },

  deleteLog: async (id: string): Promise<void> => {
    await apiClient.delete(`/health/logs/${id}`)
  },
}

// ── Sleep logs ────────────────────────────────────────────────
export const sleepApi = {
  list: async (params?: { start_date?: string; end_date?: string; limit?: number }): Promise<SleepLog[]> => {
    const res = await apiClient.get<SleepLog[]>('/sleep', { params })
    return res.data
  },

  create: async (data: {
    sleep_date: string
    bedtime: string
    wake_time: string
    quality_score?: number
    interruptions?: number
    source?: string
  }): Promise<SleepLog> => {
    const res = await apiClient.post<SleepLog>('/sleep', data)
    return res.data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/sleep/${id}`)
  },
}

// ── Activity logs ─────────────────────────────────────────────
export const activityApi = {
  list: async (params?: { start_date?: string; end_date?: string; limit?: number }): Promise<ActivityLog[]> => {
    const res = await apiClient.get<ActivityLog[]>('/activity', { params })
    return res.data
  },

  create: async (data: {
    activity_date: string
    activity_type: string
    duration_min?: number
    calories_burned?: number
    steps?: number
    intensity?: number
    source?: string
  }): Promise<ActivityLog> => {
    const res = await apiClient.post<ActivityLog>('/activity', data)
    return res.data
  },
}

// ── Recommendation engine ─────────────────────────────────────
export const recommendationApi = {
  generate: async (metrics: HealthMetrics): Promise<HealthInsightsResponse> => {
    const res = await apiClient.post<HealthInsightsResponse>(
      '/recommendations',
      metrics
    )
    return res.data
  },

  getQuick: async (metrics: HealthMetrics): Promise<HealthInsightsResponse> => {
    const res = await apiClient.post<HealthInsightsResponse>(
      '/recommendations/quick',
      metrics
    )
    return res.data
  },
}
