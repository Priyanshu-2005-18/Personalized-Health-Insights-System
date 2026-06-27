import { clsx, type ClassValue } from 'clsx'
import type { Priority, Category } from '../types'

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
  })
}

export function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export function today(): string {
  return new Date().toISOString().split('T')[0]
}

export function scoreColor(score: number): string {
  if (score >= 85) return '#1D9E75'
  if (score >= 70) return '#14b8a6'
  if (score >= 55) return '#eab308'
  if (score >= 40) return '#f97316'
  return '#ef4444'
}

export function scoreLabel(score: number): string {
  if (score >= 85) return 'Excellent'
  if (score >= 70) return 'Good'
  if (score >= 55) return 'Fair'
  if (score >= 40) return 'Poor'
  return 'Critical'
}

export function priorityClass(priority: Priority): string {
  const map: Record<Priority, string> = {
    critical: 'priority-critical',
    high:     'priority-high',
    medium:   'priority-medium',
    low:      'priority-low',
  }
  return map[priority]
}

export function priorityLabel(priority: Priority): string {
  const map: Record<Priority, string> = {
    critical: '🆘 Critical',
    high:     '🔴 High',
    medium:   '🟡 Medium',
    low:      '🟢 Low',
  }
  return map[priority]
}

export function categoryLabel(cat: Category): string {
  const map: Record<Category, string> = {
    sleep:      'Sleep',
    activity:   'Activity',
    nutrition:  'Nutrition',
    hydration:  'Hydration',
    stress:     'Stress',
    heart_rate: 'Heart Rate',
    general:    'General',
  }
  return map[cat]
}

export function categoryIcon(cat: Category): string {
  const map: Record<Category, string> = {
    sleep:      '😴',
    activity:   '🏃',
    nutrition:  '🍽️',
    hydration:  '💧',
    stress:     '🧘',
    heart_rate: '❤️',
    general:    '💡',
  }
  return map[cat]
}

export function statusColor(status: string): string {
  const map: Record<string, string> = {
    optimal:  'text-teal-600 bg-teal-50',
    good:     'text-yellow-600 bg-yellow-50',
    fair:     'text-orange-500 bg-orange-50',
    poor:     'text-red-500 bg-red-50',
    critical: 'text-red-700 bg-red-100',
    unknown:  'text-gray-400 bg-gray-50',
  }
  return map[status] ?? 'text-gray-400 bg-gray-50'
}

export function bmiLabel(bmi: number): string {
  if (bmi < 18.5) return 'Underweight'
  if (bmi < 25)   return 'Normal'
  if (bmi < 30)   return 'Overweight'
  return 'Obese'
}

export function activityLevelLabel(level: string): string {
  const map: Record<string, string> = {
    sedentary:         'Sedentary',
    lightly_active:    'Lightly Active',
    moderately_active: 'Moderately Active',
    very_active:       'Very Active',
    extra_active:      'Extra Active',
  }
  return map[level] ?? level
}

export function getApiError(err: unknown): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const e = err as { response?: { data?: { detail?: string } } }
    return e.response?.data?.detail ?? 'Something went wrong'
  }
  return 'Something went wrong'
}

// Re-export formatters and constants for convenience
export * from './formatters'
export * from './constants'
export * from './validators'
