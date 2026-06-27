// ── Auth ─────────────────────────────────────────────────────
export interface User {
  id: string
  email: string
  username: string
  full_name: string | null
  role: string
  is_active: boolean
  is_verified: boolean
  last_login_at: string | null
  created_at: string
  updated_at: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
  confirm_password: string
  full_name?: string
}

// ── Profile ──────────────────────────────────────────────────
export interface UserProfile {
  id: string
  user_id: string
  first_name: string
  last_name: string
  date_of_birth: string | null
  gender: 'male' | 'female' | 'non_binary' | 'prefer_not_to_say' | null
  height_cm: number | null
  weight_kg: number | null
  activity_level: ActivityLevel | null
  health_goals: string[] | null
  medical_conditions: string[] | null
  avatar_url: string | null
  timezone: string
  updated_at: string
}

export type ActivityLevel =
  | 'sedentary'
  | 'lightly_active'
  | 'moderately_active'
  | 'very_active'
  | 'extra_active'

// ── Health Log ───────────────────────────────────────────────
export interface HealthLogCreate {
  log_date: string
  mood_score?: number | null
  stress_level?: number | null
  energy_level?: number | null
  water_ml?: number | null
  sleep_hours?: number | null
  steps?: number | null
  calories?: number | null
  heart_rate_bpm?: number | null
  notes?: string | null
}

export interface HealthLog extends HealthLogCreate {
  id: string
  user_id: string
  health_score?: number | null
  created_at: string
}

// ── Health Metrics (for recommendation engine) ───────────────
export interface HealthMetrics {
  sleep_hours?: number | null
  steps?: number | null
  calories?: number | null
  water_intake_ml?: number | null
  stress_level?: number | null
  heart_rate_bpm?: number | null
  health_score?: number | null
}

// ── Recommendations ──────────────────────────────────────────
export type Priority = 'critical' | 'high' | 'medium' | 'low'
export type Category =
  | 'sleep'
  | 'activity'
  | 'nutrition'
  | 'hydration'
  | 'stress'
  | 'heart_rate'
  | 'general'

export interface ActionStep {
  order: number
  description: string
  duration: string | null
  frequency: string | null
}

export interface Recommendation {
  id: string
  category: Category
  priority: Priority
  title: string
  summary: string
  detail: string
  actions: ActionStep[]
  metric_value: number | null
  target_value: string | null
  icon: string
  score_impact: number
  tags: string[]
}

export interface MetricStatus {
  name: string
  value: number | null
  unit: string
  status: 'optimal' | 'good' | 'fair' | 'poor' | 'critical' | 'unknown'
  status_label: string
  target: string
  score: number
}

export interface HealthInsightsResponse {
  health_score: number
  health_score_label: 'Excellent' | 'Good' | 'Fair' | 'Poor' | 'Critical'
  overall_summary: string
  metric_statuses: MetricStatus[]
  recommendations: Recommendation[]
  total_count: number
  critical_count: number
  high_count: number
  score_improvement_potential: number
  generated_at: string
}

// ── Sleep / Activity / Nutrition ────────────────────────────
export interface SleepLog {
  id: string
  user_id: string
  sleep_date: string
  bedtime: string
  wake_time: string
  duration_min: number | null
  quality_score: number | null
  interruptions: number
  source: string
  created_at: string
}

export interface ActivityLog {
  id: string
  user_id: string
  activity_date: string
  activity_type: string
  duration_min: number | null
  calories_burned: number | null
  steps: number | null
  intensity: number | null
  source: string
  created_at: string
}

// ── API Generic ──────────────────────────────────────────────
export interface ApiError {
  detail: string
  errors?: Array<{ field: string; message: string; type: string }>
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// Re-export API-layer types
export * from './api'
