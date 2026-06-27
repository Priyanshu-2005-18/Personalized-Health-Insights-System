import { useEffect, useState } from 'react'
import {
  User, Edit3, Save, X, Calendar, Ruler,
  Weight, Activity, Target, ShieldCheck,
} from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { profileApi } from '../api/profile'
import { authApi } from '../api/auth'
import { Input } from '../components/common/Input'
import { Select } from '../components/common/Select'
import { Button } from '../components/common/Button'
import { Alert } from '../components/common/Alert'
import { Card, CardHeader, CardTitle } from '../components/common/Card'
import { Badge } from '../components/common/Badge'
import { Spinner } from '../components/common/Spinner'
import type { UserProfile } from '../types'
import { activityLevelLabel, bmiLabel, formatDate, getApiError } from '../utils'

const GENDER_OPTIONS = [
  { value: 'male',              label: 'Male' },
  { value: 'female',            label: 'Female' },
  { value: 'non_binary',        label: 'Non-binary' },
  { value: 'prefer_not_to_say', label: 'Prefer not to say' },
]

const ACTIVITY_OPTIONS = [
  { value: 'sedentary',          label: 'Sedentary (desk job, little exercise)' },
  { value: 'lightly_active',     label: 'Lightly Active (1–3 days/week)' },
  { value: 'moderately_active',  label: 'Moderately Active (3–5 days/week)' },
  { value: 'very_active',        label: 'Very Active (6–7 days/week)' },
  { value: 'extra_active',       label: 'Extra Active (physical job + training)' },
]

const HEALTH_GOALS = [
  'lose_weight', 'gain_muscle', 'improve_sleep', 'reduce_stress',
  'increase_energy', 'improve_cardiovascular', 'better_nutrition',
  'increase_flexibility', 'quit_smoking', 'reduce_alcohol',
]

const GOAL_LABELS: Record<string, string> = {
  lose_weight:            '⚖️ Lose Weight',
  gain_muscle:            '💪 Gain Muscle',
  improve_sleep:          '😴 Improve Sleep',
  reduce_stress:          '🧘 Reduce Stress',
  increase_energy:        '⚡ Increase Energy',
  improve_cardiovascular: '❤️ Heart Health',
  better_nutrition:       '🥗 Better Nutrition',
  increase_flexibility:   '🤸 Flexibility',
  quit_smoking:           '🚭 Quit Smoking',
  reduce_alcohol:         '🍷 Reduce Alcohol',
}

// ─── BMI gauge ────────────────────────────────────────────────
function BmiGauge({ bmi }: { bmi: number }) {
  const label = bmiLabel(bmi)
  const colorMap: Record<string, string> = {
    Underweight: '#0891b2',
    Normal:      '#1D9E75',
    Overweight:  '#f97316',
    Obese:       '#ef4444',
  }
  const color = colorMap[label] ?? '#94a3b8'
  const pct   = Math.min(100, Math.max(0, ((bmi - 10) / (45 - 10)) * 100))

  return (
    <div className="p-4 bg-health-surface rounded-xl">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-health-muted">BMI</span>
        <span className="font-bold text-lg" style={{ color }}>{bmi.toFixed(1)}</span>
      </div>
      <div className="h-2 bg-health-border rounded-full overflow-hidden mb-1.5">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-health-muted">
        <span>Underweight</span><span>Normal</span>
        <span>Overweight</span><span>Obese</span>
      </div>
      <p className="text-center text-sm font-semibold mt-2" style={{ color }}>{label}</p>
    </div>
  )
}

export function ProfilePage() {
  const { user, setUser } = useAuthStore()
  const [profile, setProfile]   = useState<UserProfile | null>(null)
  const [editing, setEditing]   = useState(false)
  const [form, setForm]         = useState<Partial<UserProfile>>({})
  const [loading, setLoading]   = useState(true)
  const [saving, setSaving]     = useState(false)
  const [success, setSuccess]   = useState(false)
  const [error, setError]       = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const [p, me] = await Promise.all([profileApi.get(), authApi.getMe()])
        setProfile(p)
        setUser(me)
        setForm(p)
      } catch {
        // Profile may not exist yet
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const startEdit = () => {
    setForm(profile ?? {})
    setEditing(true)
    setSuccess(false)
    setError(null)
  }

  const cancelEdit = () => {
    setForm(profile ?? {})
    setEditing(false)
    setError(null)
  }

  const set = <K extends keyof UserProfile>(key: K) =>
    (val: UserProfile[K]) => setForm((f) => ({ ...f, [key]: val }))

  const toggleGoal = (goal: string) => {
    const current = form.health_goals ?? []
    set('health_goals')(
      current.includes(goal) ? current.filter((g) => g !== goal) : [...current, goal]
    )
  }

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      const saved = profile
        ? await profileApi.update(form)
        : await profileApi.create(form)
      setProfile(saved)
      setEditing(false)
      setSuccess(true)
    } catch (err) {
      setError(getApiError(err))
    } finally {
      setSaving(false)
    }
  }

  const bmi =
    form.weight_kg && form.height_cm
      ? form.weight_kg / Math.pow(form.height_cm / 100, 2)
      : null

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" label="Loading profile…" />
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-up">

      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-health-slate">Profile</h1>
          <p className="text-health-muted text-sm mt-1">Manage your health profile and preferences.</p>
        </div>
        {!editing ? (
          <Button
            variant="secondary"
            size="sm"
            leftIcon={<Edit3 className="h-4 w-4" />}
            onClick={startEdit}
          >
            Edit Profile
          </Button>
        ) : (
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" leftIcon={<X className="h-4 w-4" />} onClick={cancelEdit}>
              Cancel
            </Button>
            <Button size="sm" leftIcon={<Save className="h-4 w-4" />} onClick={handleSave} loading={saving}>
              Save
            </Button>
          </div>
        )}
      </div>

      {success && (
        <Alert variant="success" message="Profile updated successfully!" onDismiss={() => setSuccess(false)} />
      )}
      {error && (
        <Alert variant="error" message={error} onDismiss={() => setError(null)} />
      )}

      {/* ── Avatar + account info ──────────────────────────────── */}
      <Card>
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-teal-100 rounded-2xl flex items-center justify-center shrink-0">
            <span className="text-2xl font-bold text-teal-700">
              {user?.username?.[0]?.toUpperCase() ?? 'U'}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="font-bold text-health-slate text-lg">
              {profile ? `${profile.first_name} ${profile.last_name}` : user?.username}
            </h2>
            <p className="text-health-muted text-sm">{user?.email}</p>
            <div className="flex items-center gap-2 mt-2">
              <Badge variant={user?.is_verified ? 'success' : 'warning'}>
                <ShieldCheck className="h-3 w-3" />
                {user?.is_verified ? 'Verified' : 'Unverified'}
              </Badge>
              <Badge variant="muted">@{user?.username}</Badge>
              {user?.created_at && (
                <Badge variant="muted">
                  Joined {formatDate(user.created_at)}
                </Badge>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* ── Personal details ───────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-4 w-4 text-health-muted" />
            Personal Details
          </CardTitle>
        </CardHeader>

        {editing ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="First name"
                value={form.first_name ?? ''}
                onChange={(e) => set('first_name')(e.target.value)}
                required
              />
              <Input
                label="Last name"
                value={form.last_name ?? ''}
                onChange={(e) => set('last_name')(e.target.value)}
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Date of birth"
                type="date"
                value={form.date_of_birth ? String(form.date_of_birth).slice(0, 10) : ''}
                onChange={(e) => set('date_of_birth')(e.target.value as any)}
                leftIcon={<Calendar className="h-4 w-4" />}
              />
              <Select
                label="Gender"
                value={form.gender ?? ''}
                onChange={(e) => set('gender')(e.target.value as any)}
                options={GENDER_OPTIONS}
                placeholder="Select…"
              />
            </div>
            <Input
              label="Timezone"
              value={form.timezone ?? 'UTC'}
              onChange={(e) => set('timezone')(e.target.value)}
              hint="e.g. Asia/Kolkata, Europe/London, America/New_York"
            />
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 text-sm">
            {[
              { label: 'First name',    value: profile?.first_name },
              { label: 'Last name',     value: profile?.last_name },
              { label: 'Date of birth', value: profile?.date_of_birth ? formatDate(String(profile.date_of_birth)) : null },
              { label: 'Gender',        value: profile?.gender?.replace(/_/g, ' ') },
              { label: 'Timezone',      value: profile?.timezone },
            ].map(({ label, value }) => (
              <div key={label}>
                <p className="text-xs text-health-muted font-medium mb-0.5">{label}</p>
                <p className="font-medium text-health-slate">{value ?? <span className="text-health-muted">—</span>}</p>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* ── Body metrics ───────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Ruler className="h-4 w-4 text-health-muted" />
            Body Metrics
          </CardTitle>
        </CardHeader>

        {editing ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Height"
                type="number"
                min={100} max={250} step={0.5}
                value={form.height_cm ?? ''}
                onChange={(e) => set('height_cm')(e.target.value ? +e.target.value : null as any)}
                leftIcon={<Ruler className="h-4 w-4" />}
                hint="centimetres"
                placeholder="175"
              />
              <Input
                label="Weight"
                type="number"
                min={30} max={500} step={0.5}
                value={form.weight_kg ?? ''}
                onChange={(e) => set('weight_kg')(e.target.value ? +e.target.value : null as any)}
                leftIcon={<Weight className="h-4 w-4" />}
                hint="kilograms"
                placeholder="70"
              />
            </div>
            {bmi && <BmiGauge bmi={bmi} />}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 text-sm mb-4">
            {[
              { label: 'Height', value: profile?.height_cm ? `${profile.height_cm} cm` : null },
              { label: 'Weight', value: profile?.weight_kg ? `${profile.weight_kg} kg` : null },
            ].map(({ label, value }) => (
              <div key={label}>
                <p className="text-xs text-health-muted font-medium mb-0.5">{label}</p>
                <p className="font-medium text-health-slate">{value ?? <span className="text-health-muted">—</span>}</p>
              </div>
            ))}
          </div>
        )}
        {!editing && bmi && <BmiGauge bmi={bmi} />}
      </Card>

      {/* ── Activity level ─────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-health-muted" />
            Activity Level
          </CardTitle>
        </CardHeader>
        {editing ? (
          <Select
            label="Typical activity level"
            value={form.activity_level ?? ''}
            onChange={(e) => set('activity_level')(e.target.value as any)}
            options={ACTIVITY_OPTIONS}
            placeholder="Select your activity level…"
            hint="Used to personalise calorie and step recommendations"
          />
        ) : (
          <div>
            <p className="text-xs text-health-muted font-medium mb-1">Activity level</p>
            <p className="font-medium text-health-slate">
              {profile?.activity_level
                ? activityLevelLabel(profile.activity_level)
                : <span className="text-health-muted">Not set</span>
              }
            </p>
          </div>
        )}
      </Card>

      {/* ── Health goals ───────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-4 w-4 text-health-muted" />
            Health Goals
          </CardTitle>
          {!editing && (
            <Badge variant="muted">{profile?.health_goals?.length ?? 0} selected</Badge>
          )}
        </CardHeader>
        <div className="flex flex-wrap gap-2">
          {HEALTH_GOALS.map((goal) => {
            const active = editing
              ? (form.health_goals ?? []).includes(goal)
              : (profile?.health_goals ?? []).includes(goal)
            return (
              <button
                key={goal}
                type="button"
                disabled={!editing}
                onClick={() => editing && toggleGoal(goal)}
                className={`text-sm px-3 py-1.5 rounded-full border font-medium transition-all ${
                  active
                    ? 'bg-teal-50 border-teal-400 text-teal-700'
                    : editing
                    ? 'bg-white border-health-border text-health-muted hover:border-teal-300 hover:text-teal-600'
                    : 'bg-health-surface border-health-border text-health-muted cursor-default opacity-60'
                }`}
              >
                {GOAL_LABELS[goal] ?? goal}
              </button>
            )
          })}
        </div>
      </Card>
    </div>
  )
}
