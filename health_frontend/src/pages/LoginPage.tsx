import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Mail, Lock, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { Input } from '../components/common/Input'
import { Button } from '../components/common/Button'
import { Alert } from '../components/common/Alert'
import { getApiError } from '../utils'

export function LoginPage() {
  const { login } = useAuth()
  const [form, setForm] = useState({ email: '', password: '' })
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(form)
    } catch (err) {
      setError(getApiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="animate-fade-up">
      <h1 className="text-2xl font-bold text-health-slate mb-1">Welcome back</h1>
      <p className="text-health-muted text-sm mb-8">Sign in to your VitalIQ account</p>

      {error && (
        <Alert variant="error" message={error} className="mb-5" onDismiss={() => setError(null)} />
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Email address"
          type="email"
          placeholder="you@example.com"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          leftIcon={<Mail className="h-4 w-4" />}
          required
          autoComplete="email"
        />

        <Input
          label="Password"
          type={showPw ? 'text' : 'password'}
          placeholder="Enter your password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          leftIcon={<Lock className="h-4 w-4" />}
          rightIcon={
            <button type="button" onClick={() => setShowPw(!showPw)} className="focus:outline-none">
              {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          }
          required
          autoComplete="current-password"
        />

        <Button type="submit" loading={loading} fullWidth size="lg" className="mt-2">
          Sign in
        </Button>
      </form>

      <p className="text-center text-sm text-health-muted mt-6">
        Don't have an account?{' '}
        <Link to="/register" className="font-medium text-health-green hover:underline">
          Create one free
        </Link>
      </p>

      {/* Demo credentials hint */}
      <div className="mt-8 p-4 bg-health-surface border border-health-border rounded-xl">
        <p className="text-xs font-medium text-health-muted mb-2">Demo credentials</p>
        <p className="text-xs text-health-muted font-mono">
          email: demo@vitaliq.app<br />
          password: Demo@12345
        </p>
      </div>
    </div>
  )
}
