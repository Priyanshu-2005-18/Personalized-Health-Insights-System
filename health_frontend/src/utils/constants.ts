/**
 * constants.ts
 * ============
 * Application-wide constants.
 * Import from here — never scatter magic numbers through components.
 */

// ── App ───────────────────────────────────────────────────────
export const APP_NAME    = 'VitalIQ'
export const APP_VERSION = '1.0.0'
export const APP_TAGLINE = 'Personalized Health Insights'

// ── API ───────────────────────────────────────────────────────
export const API_TIMEOUT_MS      = 15_000
export const TOKEN_REFRESH_GRACE = 60    // refresh 60s before expiry

// ── Pagination ────────────────────────────────────────────────
export const DEFAULT_PAGE_SIZE  = 20
export const MAX_PAGE_SIZE      = 100
export const LOG_LIST_LIMIT     = 14   // days shown in dashboard trend

// ── Health metric limits ──────────────────────────────────────
export const METRIC_LIMITS = {
  sleep_hours:     { min: 0,   max: 24,      step: 0.5  },
  steps:           { min: 0,   max: 100_000, step: 100  },
  calories:        { min: 0,   max: 10_000,  step: 50   },
  water_intake_ml: { min: 0,   max: 10_000,  step: 250  },
  stress_level:    { min: 1,   max: 10,      step: 1    },
  heart_rate_bpm:  { min: 30,  max: 250,     step: 1    },
  mood_score:      { min: 1,   max: 10,      step: 1    },
  energy_level:    { min: 1,   max: 10,      step: 1    },
} as const

// ── Health score bands ────────────────────────────────────────
export const SCORE_BANDS = {
  EXCELLENT: { min: 85,  label: 'Excellent', color: '#1D9E75' },
  GOOD:      { min: 70,  label: 'Good',      color: '#14b8a6' },
  FAIR:      { min: 55,  label: 'Fair',      color: '#eab308' },
  POOR:      { min: 40,  label: 'Poor',      color: '#f97316' },
  CRITICAL:  { min: 0,   label: 'Critical',  color: '#ef4444' },
} as const

// ── Metric targets (for display) ──────────────────────────────
export const METRIC_TARGETS: Record<string, string> = {
  sleep_hours:     '7–9 hours',
  steps:           '10,000 steps',
  calories:        '1,600–2,400 kcal',
  water_intake_ml: '2,000–3,000 ml',
  stress_level:    '1–3 (low)',
  heart_rate_bpm:  '55–75 bpm',
  mood_score:      '7–10',
  energy_level:    '7–10',
}

// ── Metric icons ──────────────────────────────────────────────
export const METRIC_ICONS: Record<string, string> = {
  sleep_hours:     '😴',
  steps:           '🚶',
  calories:        '🍽️',
  water_intake_ml: '💧',
  stress_level:    '🧘',
  heart_rate_bpm:  '❤️',
  mood_score:      '😊',
  energy_level:    '⚡',
}

// ── Category config ───────────────────────────────────────────
export const CATEGORY_CONFIG = {
  sleep:      { label: 'Sleep',        icon: '😴', color: '#8b5cf6' },
  activity:   { label: 'Activity',     icon: '🏃', color: '#1D9E75' },
  nutrition:  { label: 'Nutrition',    icon: '🍽️', color: '#f97316' },
  hydration:  { label: 'Hydration',    icon: '💧', color: '#0891b2' },
  stress:     { label: 'Stress',       icon: '🧘', color: '#ef4444' },
  heart_rate: { label: 'Heart Rate',   icon: '❤️', color: '#ec4899' },
  general:    { label: 'General',      icon: '💡', color: '#94a3b8' },
} as const

// ── Priority config ───────────────────────────────────────────
export const PRIORITY_CONFIG = {
  critical: { label: 'Critical', color: '#ef4444', bg: '#fef2f2', icon: '🆘' },
  high:     { label: 'High',     color: '#f97316', bg: '#fff7ed', icon: '🔴' },
  medium:   { label: 'Medium',   color: '#eab308', bg: '#fefce8', icon: '🟡' },
  low:      { label: 'Low',      color: '#1D9E75', bg: '#f0fdfa', icon: '🟢' },
} as const

// ── Local storage keys ────────────────────────────────────────
export const LS_KEYS = {
  ACCESS_TOKEN:   'access_token',
  REFRESH_TOKEN:  'refresh_token',
  AUTH_STATE:     'health-auth',
  THEME:          'health-theme',
  LAST_LOG_DATE:  'last-log-date',
} as const

// ── Route paths ───────────────────────────────────────────────
export const ROUTES = {
  LOGIN:            '/login',
  REGISTER:         '/register',
  DASHBOARD:        '/dashboard',
  HEALTH_FORM:      '/health-form',
  RECOMMENDATIONS:  '/recommendations',
  PROFILE:          '/profile',
} as const

// ── Nutrition info ────────────────────────────────────────────
export const WATER_GLASS_ML  = 250   // ml per standard glass
export const CALORIE_TARGETS = {
  sedentary:          1800,
  lightly_active:     2000,
  moderately_active:  2200,
  very_active:        2600,
  extra_active:       3000,
} as const
