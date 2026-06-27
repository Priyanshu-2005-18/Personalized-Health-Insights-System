import { useEffect, useState } from 'react'
import {
  Moon, Footprints, Flame, Droplets, Brain,
  Heart, FileText, Save, RotateCcw, CheckCircle2,
} from 'lucide-react'
import { healthApi } from '../api/health'
import { Input } from '../components/common/Input'
import { Button } from '../components/common/Button'
import { Alert } from '../components/common/Alert'
import { Card, CardHeader, CardTitle } from '../components/common/Card'
import { Badge } from '../components/common/Badge'
import { today, getApiError } from '../utils'
import type { HealthLog } from '../types'

// ─── Slider component ──────────────────────────────────────────
function RangeSlider({
  label, value, onChange, min = 1, max = 10, step = 1,
  leftLabel, rightLabel, icon, color = '#1D9E75',
  hint,
}: {
  label: string; value: number | ''; onChange: (v: number | '') => void
  min?: number; max?: number; step?: number
  leftLabel?: string; rightLabel?: string
  icon?: React.ReactNode; color?: string; hint?: string
}) {
  const pct = value !== '' ? ((+value - min) / (max - min)) * 100 : 0

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-health-slate flex items-center gap-1.5">
          {icon && <span style={{ color }}>{icon}</span>}
          {label}
        </label>
        <span
          className="text-sm font-bold px-2.5 py-0.5 rounded-full"
          style={{ color, backgroundColor: `${color}18` }}
        >
          {value !== '' ? value : '—'}
        </span>
      </div>
      <div className="relative">
        <input
          type="range"
          min={min} max={max} step={step}
          value={value !== '' ? value : min}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-full h-2 rounded-full appearance-none cursor-pointer"
          style={{
            background: value !== ''
              ? `linear-gradient(to right, ${color} ${pct}%, #e2e8f0 ${pct}%)`
              : '#e2e8f0',
          }}
        />
      </div>
      {(leftLabel || rightLabel) && (
        <div className="flex justify-between text-[10px] text-health-muted">
          <span>{leftLabel}</span>
          <span>{rightLabel}</span>
        </div>
      )}
      {hint && <p className="text-xs text-health-muted">{hint}</p>}
    </div>
  )
}

// ─── Number input with increment buttons ───────────────────────
function NumericInput({
  label, value, onChange, min = 0, max, step = 1,
  unit, icon, color = '#1D9E75', hint, placeholder,
}: {
  label: string; value: number | ''; onChange: (v: number | '') => void
  min?: number; max?: number; step?: number
  unit?: string; icon?: React.ReactNode; color?: string
  hint?: string; placeholder?: string
}) {
  const increment = () => {
    const v = value !== '' ? +value : 0
    if (max === undefined || v + step <= max) onChange(+(v + step).toFixed(2))
  }
  const decrement = () => {
    const v = value !== '' ? +value : 0
    if (v - step >= min) onChange(+(v - step).toFixed(2))
  }

  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium text-health-slate flex items-center gap-1.5">
        {icon && <span style={{ color }}>{icon}</span>}
        {label}
      </label>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={decrement}
          className="w-9 h-9 flex items-center justify-center rounded-xl border border-health-border bg-white hover:bg-health-surface text-health-muted text-lg font-medium transition-all active:scale-95"
        >
          −
        </button>
        <div className="relative flex-1">
          <input
            type="number"
            min={min} max={max} step={step}
            value={value}
            onChange={(e) => onChange(e.target.value === '' ? '' : Number(e.target.value))}
            placeholder={placeholder ?? '0'}
            className="input-base text-center pr-12"
          />
          {unit && (
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-health-muted font-medium">
              {unit}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={increment}
          className="w-9 h-9 flex items-center justify-center rounded-xl border border-health-border bg-white hover:bg-health-surface text-health-muted text-lg font-medium transition-all active:scale-95"
        >
          +
        </button>
      </div>
      {hint && <p className="text-xs text-health-muted">{hint}</p>}
    </div>
  )
}

// ─── Form state ────────────────────────────────────────────────
interface FormState {
  log_date:        string
  // Daily log fields
  mood_score:      number | ''
  stress_level:    number | ''
  energy_level:    number | ''
  water_ml:        number | ''
  notes:           string
  // Extended metrics (sent to recommendation engine)
  sleep_hours:     number | ''
  steps:           number | ''
  calories:        number | ''
  heart_rate_bpm:  number | ''
}

const BLANK: FormState = {
  log_date:       today(),
  mood_score:     '',
  stress_level:   '',
  energy_level:   '',
  water_ml:       '',
  notes:          '',
  sleep_hours:    '',
  steps:          '',
  calories:       '',
  heart_rate_bpm: '',
}

export function HealthFormPage() {
  const [form, setForm]         = useState<FormState>(BLANK)
  const [loading, setLoading]   = useState(false)
  const [success, setSuccess]   = useState(false)
  const [error, setError]       = useState<string | null>(null)
  const [existingId, setExistingId] = useState<string | null>(null)

  // Pre-fill if today's log exists
  useEffect(() => {
    healthApi.getTodayLog().then((log) => {
      if (log) {
        setExistingId(log.id)
        setForm((f) => ({
          ...f,
          log_date:     log.log_date ?? f.log_date,
          mood_score:   log.mood_score   ?? '',
          stress_level: log.stress_level ?? '',
          energy_level: log.energy_level ?? '',
          water_ml:     log.water_ml     ?? '',
          sleep_hours:  log.sleep_hours  ?? '',
          steps:        log.steps        ?? '',
          calories:     log.calories     ?? '',
          heart_rate_bpm: log.heart_rate_bpm ?? '',
          notes:        log.notes        ?? '',
        }))
      }
    })
  }, [])

  const set = <K extends keyof FormState>(key: K) =>
    (val: FormState[K]) => setForm((f) => ({ ...f, [key]: val }))

  const handleReset = () => {
    setForm({ ...BLANK, log_date: today() })
    setExistingId(null)
    setSuccess(false)
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(false)

    // At least one metric required
    const hasMetric = [
      form.mood_score, form.stress_level, form.energy_level,
      form.water_ml, form.sleep_hours, form.steps,
      form.calories, form.heart_rate_bpm,
    ].some((v) => v !== '')

    if (!hasMetric && !form.notes) {
      setError('Please fill in at least one health metric before saving.')
      return
    }

    setLoading(true)
    try {
      const payload = {
        log_date:     form.log_date,
        mood_score:   form.mood_score   !== '' ? +form.mood_score   : undefined,
        stress_level: form.stress_level !== '' ? +form.stress_level : undefined,
        energy_level: form.energy_level !== '' ? +form.energy_level : undefined,
        water_ml:     form.water_ml     !== '' ? +form.water_ml     : undefined,
        sleep_hours:  form.sleep_hours  !== '' ? +form.sleep_hours  : undefined,
        steps:        form.steps        !== '' ? +form.steps        : undefined,
        calories:     form.calories     !== '' ? +form.calories     : undefined,
        heart_rate_bpm: form.heart_rate_bpm !== '' ? +form.heart_rate_bpm : undefined,
        notes:        form.notes || undefined,
      } as any

      if (existingId) {
        await healthApi.updateLog(existingId, payload)
      } else {
        const created = await healthApi.createLog(payload)
        setExistingId(created.id)
      }
      setSuccess(true)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (err) {
      setError(getApiError(err))
    } finally {
      setLoading(false)
    }
  }

  // Completion counter
  const filled = [
    form.mood_score, form.stress_level, form.energy_level, form.water_ml,
    form.sleep_hours, form.steps, form.calories, form.heart_rate_bpm,
  ].filter((v) => v !== '').length
  const total = 8
  const pct   = Math.round((filled / total) * 100)

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-up">

      {/* ── Header ─────────────────────────────────────────────── */}
      <div>
        <h1 className="text-2xl font-bold text-health-slate">Log Health Data</h1>
        <p className="text-health-muted text-sm mt-1">
          Track your daily metrics to get personalised health insights.
        </p>
      </div>

      {/* ── Progress bar ───────────────────────────────────────── */}
      <Card padding={false} className="p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-health-slate">
            Entry completeness
          </span>
          <span className="text-sm font-semibold text-health-green">{pct}%</span>
        </div>
        <div className="h-2 bg-health-surface rounded-full overflow-hidden">
          <div
            className="h-full bg-health-green rounded-full transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className="text-xs text-health-muted mt-1.5">
          {filled}/{total} metrics filled — more data = better recommendations
        </p>
      </Card>

      {success && (
        <Alert
          variant="success"
          title="Saved successfully!"
          message="Your health data has been logged. Head to Recommendations to see your personalised insights."
          onDismiss={() => setSuccess(false)}
        />
      )}
      {error && (
        <Alert variant="error" message={error} onDismiss={() => setError(null)} />
      )}

      <form onSubmit={handleSubmit} className="space-y-5">

        {/* ── Date ─────────────────────────────────────────────── */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-health-muted" />
              Entry Date
            </CardTitle>
            {existingId && <Badge variant="warning">Updating existing log</Badge>}
          </CardHeader>
          <Input
            type="date"
            value={form.log_date}
            onChange={(e) => set('log_date')(e.target.value)}
            max={today()}
            required
          />
        </Card>

        {/* ── Sleep ────────────────────────────────────────────── */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Moon className="h-4 w-4 text-purple-500" />
              Sleep
            </CardTitle>
            <Badge variant="muted">Target: 7–9 hours</Badge>
          </CardHeader>
          <NumericInput
            label="Sleep duration"
            value={form.sleep_hours}
            onChange={set('sleep_hours')}
            min={0} max={24} step={0.5}
            unit="hours"
            color="#8b5cf6"
            hint="Total sleep last night including naps"
            placeholder="7.5"
          />
        </Card>

        {/* ── Activity ─────────────────────────────────────────── */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Footprints className="h-4 w-4 text-health-green" />
              Physical Activity
            </CardTitle>
            <Badge variant="muted">Target: 10,000 steps</Badge>
          </CardHeader>
          <NumericInput
            label="Steps taken today"
            value={form.steps}
            onChange={set('steps')}
            min={0} max={100000} step={100}
            unit="steps"
            color="#1D9E75"
            hint="Total steps from all activities"
            placeholder="8000"
          />
        </Card>

        {/* ── Nutrition ────────────────────────────────────────── */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Flame className="h-4 w-4 text-orange-500" />
              Nutrition
            </CardTitle>
            <Badge variant="muted">Target: 1,600–2,400 kcal</Badge>
          </CardHeader>
          <NumericInput
            label="Calories consumed"
            value={form.calories}
            onChange={set('calories')}
            min={0} max={10000} step={50}
            unit="kcal"
            color="#f97316"
            hint="Total dietary calories for the day"
            placeholder="2000"
          />
        </Card>

        {/* ── Hydration ────────────────────────────────────────── */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Droplets className="h-4 w-4 text-blue-500" />
              Hydration
            </CardTitle>
            <Badge variant="muted">Target: 2,000–3,000 ml</Badge>
          </CardHeader>
          <NumericInput
            label="Water intake"
            value={form.water_ml}
            onChange={set('water_ml')}
            min={0} max={10000} step={250}
            unit="ml"
            color="#0891b2"
            hint="250 ml ≈ 1 glass. Include all fluids."
            placeholder="2500"
          />
        </Card>

        {/* ── Heart Rate ───────────────────────────────────────── */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Heart className="h-4 w-4 text-pink-500" />
              Heart Rate
            </CardTitle>
            <Badge variant="muted">Target: 55–75 bpm</Badge>
          </CardHeader>
          <NumericInput
            label="Resting heart rate"
            value={form.heart_rate_bpm}
            onChange={set('heart_rate_bpm')}
            min={30} max={250} step={1}
            unit="bpm"
            color="#ec4899"
            hint="Measure first thing in the morning before getting up"
            placeholder="70"
          />
        </Card>

        {/* ── Subjective scores ────────────────────────────────── */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-4 w-4 text-red-500" />
              Wellbeing Scores
            </CardTitle>
          </CardHeader>
          <div className="space-y-6">
            <RangeSlider
              label="Mood Score"
              value={form.mood_score}
              onChange={set('mood_score')}
              min={1} max={10}
              leftLabel="Very low" rightLabel="Excellent"
              icon={<span>😊</span>}
              color="#8b5cf6"
              hint="How did you feel overall today?"
            />
            <RangeSlider
              label="Stress Level"
              value={form.stress_level}
              onChange={set('stress_level')}
              min={1} max={10}
              leftLabel="No stress" rightLabel="Extreme"
              icon={<Brain className="h-3.5 w-3.5" />}
              color="#ef4444"
              hint="How stressed did you feel today?"
            />
            <RangeSlider
              label="Energy Level"
              value={form.energy_level}
              onChange={set('energy_level')}
              min={1} max={10}
              leftLabel="Exhausted" rightLabel="High energy"
              icon={<span>⚡</span>}
              color="#eab308"
              hint="Your overall energy throughout the day"
            />
          </div>
        </Card>

        {/* ── Notes ────────────────────────────────────────────── */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-health-muted" />
              Daily Notes
            </CardTitle>
            <span className="text-xs text-health-muted">{form.notes.length}/500</span>
          </CardHeader>
          <textarea
            value={form.notes}
            onChange={(e) => set('notes')(e.target.value as any)}
            maxLength={500}
            rows={3}
            placeholder="How was your day? Any notable events, symptoms, or observations…"
            className="input-base resize-none"
          />
        </Card>

        {/* ── Actions ──────────────────────────────────────────── */}
        <div className="flex gap-3">
          <Button
            type="button"
            variant="secondary"
            onClick={handleReset}
            leftIcon={<RotateCcw className="h-4 w-4" />}
          >
            Reset
          </Button>
          <Button
            type="submit"
            loading={loading}
            fullWidth
            leftIcon={!loading ? <Save className="h-4 w-4" /> : undefined}
          >
            {existingId ? 'Update Log' : 'Save Health Log'}
          </Button>
        </div>

        {success && (
          <div className="flex items-center gap-2 justify-center text-teal-600 text-sm font-medium">
            <CheckCircle2 className="h-4 w-4" />
            Saved! Visit Recommendations to see your insights.
          </div>
        )}
      </form>
    </div>
  )
}
