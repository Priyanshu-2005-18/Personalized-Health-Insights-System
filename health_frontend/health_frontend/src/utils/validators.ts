/**
 * validators.ts
 * =============
 * Pure validation functions — return an error string on failure,
 * undefined on success.  Used in form handlers across all pages.
 */

// ── Primitives ────────────────────────────────────────────────

export function required(value: unknown, label = 'This field'): string | undefined {
  if (value === null || value === undefined || value === '') {
    return `${label} is required`
  }
}

export function minLength(value: string, min: number, label = 'Field'): string | undefined {
  if (value.length < min) return `${label} must be at least ${min} characters`
}

export function maxLength(value: string, max: number, label = 'Field'): string | undefined {
  if (value.length > max) return `${label} must be at most ${max} characters`
}

export function inRange(
  value: number, min: number, max: number, label = 'Value'
): string | undefined {
  if (value < min || value > max) {
    return `${label} must be between ${min} and ${max}`
  }
}

// ── Email ─────────────────────────────────────────────────────

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function validEmail(email: string): string | undefined {
  if (!EMAIL_RE.test(email.trim())) return 'Enter a valid email address'
}

// ── Password ──────────────────────────────────────────────────

const PASSWORD_RE = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&_\-#^]).{8,128}$/

export function strongPassword(pw: string): string | undefined {
  if (!PASSWORD_RE.test(pw)) {
    return 'Password must be 8–128 chars with uppercase, lowercase, digit, and special character'
  }
}

export function passwordsMatch(pw: string, confirm: string): string | undefined {
  if (pw !== confirm) return 'Passwords do not match'
}

// ── Health metrics ────────────────────────────────────────────

export const METRIC_RANGES = {
  sleep_hours:     { min: 0,    max: 24,     label: 'Sleep hours' },
  steps:           { min: 0,    max: 100_000, label: 'Steps' },
  calories:        { min: 0,    max: 10_000,  label: 'Calories' },
  water_intake_ml: { min: 0,    max: 10_000,  label: 'Water intake' },
  stress_level:    { min: 1,    max: 10,      label: 'Stress level' },
  heart_rate_bpm:  { min: 30,   max: 250,     label: 'Heart rate' },
  mood_score:      { min: 1,    max: 10,      label: 'Mood score' },
  energy_level:    { min: 1,    max: 10,      label: 'Energy level' },
  height_cm:       { min: 50,   max: 300,     label: 'Height' },
  weight_kg:       { min: 20,   max: 700,     label: 'Weight' },
} as const

export function validateMetric(
  key: keyof typeof METRIC_RANGES,
  value: number
): string | undefined {
  const { min, max, label } = METRIC_RANGES[key]
  return inRange(value, min, max, label)
}

// ── Composite form validators ─────────────────────────────────

export interface LoginErrors {
  email?:    string
  password?: string
}

export function validateLogin(email: string, password: string): LoginErrors {
  const errors: LoginErrors = {}
  const emailErr = required(email, 'Email') ?? validEmail(email)
  if (emailErr) errors.email = emailErr
  const pwErr = required(password, 'Password')
  if (pwErr) errors.password = pwErr
  return errors
}

export interface RegisterErrors {
  email?:            string
  username?:         string
  password?:         string
  confirm_password?: string
}

export function validateRegister(fields: {
  email:            string
  username:         string
  password:         string
  confirm_password: string
}): RegisterErrors {
  const errors: RegisterErrors = {}

  const emailErr = required(fields.email, 'Email') ?? validEmail(fields.email)
  if (emailErr) errors.email = emailErr

  const userErr = required(fields.username, 'Username') ?? minLength(fields.username, 3, 'Username')
  if (userErr) errors.username = userErr

  const pwErr = required(fields.password, 'Password') ?? strongPassword(fields.password)
  if (pwErr) errors.password = pwErr

  const confirmErr = passwordsMatch(fields.password, fields.confirm_password)
  if (confirmErr) errors.confirm_password = confirmErr

  return errors
}

// ── Utility: check if errors object is empty ──────────────────
export function hasErrors(errors: Record<string, string | undefined>): boolean {
  return Object.values(errors).some(Boolean)
}
