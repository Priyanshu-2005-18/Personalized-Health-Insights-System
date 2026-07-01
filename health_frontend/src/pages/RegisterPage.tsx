import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Mail, Lock, User, Eye, EyeOff, CheckCircle2 } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { Input } from '../components/common/Input'
import { Button } from '../components/common/Button'
import { Alert } from '../components/common/Alert'
import { getApiError } from '../utils'

interface FormState {
  email: string
  username: string
  full_name: string
  password: string
  confirm_password: string
}

const INITIAL: FormState = {
  email: '', username: '', full_name: '',
  password: '', confirm_password: '',
}

function PasswordStrength({ pw }: { pw: string }) {
  const checks = [
    { label: '8+ characters',     ok: pw.length >= 8 },
    { label: 'Uppercase letter',  ok: /[A-Z]/.test(pw) },
    { label: 'Number',            ok: /\d/.test(pw) },
    { label: 'Special character', ok: /[@$!%*?&_\-#^]/.test(pw) },
  ]
  if (!pw) return null
  return (
    <div className="grid grid-cols-2 gap-1.5 mt-1.5">
      {checks.map((c) => (
        <div key={c.label} className={`flex items-center gap-1.5 text-xs ${c.ok ? 'text-teal-600' : 'text-health-muted'}`}>
          <CheckCircle2 className={`h-3 w-3 ${c.ok ? 'text-teal-500' : 'text-health-border'}`} />
          {c.label}
        </div>
      ))}
    </div>
  )
}

export function RegisterPage() {
  const { register } = useAuth()
  const [form, setForm] = useState<FormState>(INITIAL)
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const set = (field: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (form.password !== form.confirm_password) {
      setError('Passwords do not match')
      return
    }
    setLoading(true)
    try {
      await register({
        email:            form.email,
        username:         form.username,
        full_name:        form.full_name || undefined,
        password:         form.password,
        confirm_password: form.confirm_password,
      })
    } catch (err) {
      setError(getApiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="animate-fade-up">
      <h1 className="text-2xl font-bold text-health-slate mb-1">Create your account</h1>
      <p className="text-health-muted text-sm mb-7">Start tracking your health journey today</p>

      {error && (
        <Alert variant="error" message={error} className="mb-5" onDismiss={() => setError(null)} />
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Full name"
            type="text"
            placeholder="Jane Smith"
            value={form.full_name}
            onChange={set('full_name')}
            leftIcon={<User className="h-4 w-4" />}
            autoComplete="name"
          />
          <Input
            label="Username"
            type="text"
            placeholder="janesmith"
            value={form.username}
            onChange={set('username')}
            required
            autoComplete="username"
          />
        </div>

        <Input
          label="Email address"
          type="email"
          placeholder="you@example.com"
          value={form.email}
          onChange={set('email')}
          leftIcon={<Mail className="h-4 w-4" />}
          required
          autoComplete="email"
        />

        <div>
          <Input
            label="Password"
            type={showPw ? 'text' : 'password'}
            placeholder="Create a strong password"
            value={form.password}
            onChange={set('password')}
            leftIcon={<Lock className="h-4 w-4" />}
            rightIcon={
              <button type="button" onClick={() => setShowPw(!showPw)}>
                {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            }
            required
            autoComplete="new-password"
          />
          <PasswordStrength pw={form.password} />
        </div>

        <Input
          label="Confirm password"
          type={showPw ? 'text' : 'password'}
          placeholder="Repeat your password"
          value={form.confirm_password}
          onChange={set('confirm_password')}
          leftIcon={<Lock className="h-4 w-4" />}
          error={
            form.confirm_password && form.password !== form.confirm_password
              ? 'Passwords do not match'
              : undefined
          }
          required
          autoComplete="new-password"
        />

        <Button type="submit" loading={loading} fullWidth size="lg" className="!mt-5">
          Create account
        </Button>
      </form>

      <p className="text-center text-sm text-health-muted mt-6">
        Already have an account?{' '}
        <Link to="/login" className="font-medium text-health-green hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  )
}
