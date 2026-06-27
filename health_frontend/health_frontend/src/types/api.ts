/**
 * types/api.ts
 * ============
 * API-layer TypeScript types for request/response contracts,
 * error shapes, and utility generics.
 */

// ── Generic API response wrapper ──────────────────────────────
export interface ApiResponse<T> {
  data:    T
  status:  number
  message?: string
}

// ── Pagination ────────────────────────────────────────────────
export interface PaginationParams {
  page?:   number
  size?:   number
  offset?: number
  limit?:  number
}

export interface PaginationMeta {
  total: number
  page:  number
  size:  number
  pages: number
}

// ── Error shapes ──────────────────────────────────────────────
export interface ValidationError {
  field:   string
  message: string
  type:    string
}

export interface ApiErrorBody {
  detail:  string
  errors?: ValidationError[]
  code?:   string
}

// ── Auth token payloads ───────────────────────────────────────
export interface JwtPayload {
  sub:   string     // user UUID
  email: string
  role:  string
  type:  'access' | 'refresh'
  iat:   number
  exp:   number
}

// ── Query param helpers ───────────────────────────────────────
export interface DateRangeParams {
  start_date?: string   // YYYY-MM-DD
  end_date?:   string   // YYYY-MM-DD
}

export interface HealthLogQueryParams extends DateRangeParams, PaginationParams {
  user_id?: string
}

export interface SleepLogQueryParams extends DateRangeParams, PaginationParams {}

export interface ActivityLogQueryParams extends DateRangeParams, PaginationParams {
  activity_type?: string
}

export interface NutritionLogQueryParams extends DateRangeParams, PaginationParams {}

// ── Recommendation query params ───────────────────────────────
export interface RecommendationQueryParams extends PaginationParams {
  category?:    string
  unread_only?: boolean
}

// ── Health summary params ─────────────────────────────────────
export interface HealthSummaryParams extends Required<DateRangeParams> {}

// ── Streak response ───────────────────────────────────────────
export interface StreakResponse {
  current_streak:  number
  longest_streak:  number
  last_entry_date: string | null
}

// ── Token response ────────────────────────────────────────────
export interface RefreshTokenResponse {
  access_token:  string
  refresh_token: string
  token_type:    string
}
