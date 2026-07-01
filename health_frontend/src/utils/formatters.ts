/**
 * formatters.ts
 * =============
 * Data formatting helpers used across components.
 * All functions are pure — no side effects.
 */

// ── Numbers ───────────────────────────────────────────────────

/** 8432 → "8,432" */
export function fmtNumber(n: number, decimals = 0): string {
  return n.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

/** 0.1234 → "12.3%" */
export function fmtPercent(n: number, decimals = 1): string {
  return `${(n * 100).toFixed(decimals)}%`
}

/** 7.5 hours → "7h 30m" */
export function fmtHours(hours: number): string {
  const h = Math.floor(hours)
  const m = Math.round((hours - h) * 60)
  if (h === 0) return `${m}m`
  if (m === 0) return `${h}h`
  return `${h}h ${m}m`
}

/** 150 minutes → "2h 30m" */
export function fmtMinutes(minutes: number): string {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  if (h === 0) return `${m}m`
  if (m === 0) return `${h}h`
  return `${h}h ${m}m`
}

/** 2500 ml → "2.5 L" when ≥ 1000, else "500 ml" */
export function fmtWater(ml: number): string {
  if (ml >= 1000) return `${(ml / 1000).toFixed(1)} L`
  return `${ml} ml`
}

/** 2500 steps → "2,500", 10500 → "10.5k" */
export function fmtSteps(steps: number): string {
  if (steps >= 1000) return `${(steps / 1000).toFixed(1)}k`
  return fmtNumber(steps)
}

// ── Dates ─────────────────────────────────────────────────────

/** "2024-06-15" → "Jun 15" */
export function fmtDateShort(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day:   'numeric',
  })
}

/** "2024-06-15" → "Saturday, June 15, 2024" */
export function fmtDateLong(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    weekday: 'long',
    year:    'numeric',
    month:   'long',
    day:     'numeric',
  })
}

/** "2024-06-15T10:30:00Z" → "Jun 15, 10:30 AM" */
export function fmtDateTime(isoStr: string): string {
  return new Date(isoStr).toLocaleString('en-US', {
    month:  'short',
    day:    'numeric',
    hour:   '2-digit',
    minute: '2-digit',
  })
}

/** Returns "Today", "Yesterday", or the formatted date */
export function fmtRelativeDate(dateStr: string): string {
  const date  = new Date(dateStr)
  const today = new Date()
  const yesterday = new Date()
  yesterday.setDate(today.getDate() - 1)

  if (date.toDateString() === today.toDateString())     return 'Today'
  if (date.toDateString() === yesterday.toDateString()) return 'Yesterday'
  return fmtDateShort(dateStr)
}

/** Returns "2 days ago", "1 month ago", etc. */
export function fmtTimeAgo(isoStr: string): string {
  const seconds = Math.floor((Date.now() - new Date(isoStr).getTime()) / 1000)
  const units: [string, number][] = [
    ['year',   31_536_000],
    ['month',  2_592_000],
    ['week',   604_800],
    ['day',    86_400],
    ['hour',   3_600],
    ['minute', 60],
    ['second', 1],
  ]
  for (const [unit, threshold] of units) {
    const count = Math.floor(seconds / threshold)
    if (count >= 1) {
      return `${count} ${unit}${count > 1 ? 's' : ''} ago`
    }
  }
  return 'just now'
}

// ── Health-specific ───────────────────────────────────────────

/** Format a raw metric value with its unit for display */
export function fmtMetricValue(
  key: string,
  value: number | null | undefined
): string {
  if (value == null) return '—'
  switch (key) {
    case 'sleep_hours':     return fmtHours(value)
    case 'steps':           return fmtSteps(value)
    case 'calories':        return `${fmtNumber(value)} kcal`
    case 'water_intake_ml': return fmtWater(value)
    case 'stress_level':    return `${value}/10`
    case 'heart_rate_bpm':  return `${value} bpm`
    case 'mood_score':      return `${value}/10`
    case 'energy_level':    return `${value}/10`
    case 'health_score':    return `${value.toFixed(1)}/100`
    default:                return String(value)
  }
}

/** "lose_weight" → "Lose Weight" */
export function fmtGoalLabel(goal: string): string {
  return goal.split('_').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
}

/** "moderately_active" → "Moderately Active" */
export function fmtActivityLevel(level: string): string {
  return fmtGoalLabel(level)
}
