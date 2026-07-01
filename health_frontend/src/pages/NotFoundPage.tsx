import { Link } from 'react-router-dom'
import { Home, ArrowLeft } from 'lucide-react'
import { Button } from '../components/common/Button'

export function NotFoundPage() {
  return (
    <div className="min-h-screen bg-health-surface flex items-center justify-center p-6">
      <div className="text-center max-w-md animate-fade-up">
        {/* Illustration */}
        <div className="w-24 h-24 bg-teal-50 rounded-3xl flex items-center justify-center mx-auto mb-6">
          <span className="text-5xl">🔍</span>
        </div>

        <h1 className="text-6xl font-bold text-health-green mb-2">404</h1>
        <h2 className="text-xl font-semibold text-health-slate mb-3">Page not found</h2>
        <p className="text-health-muted text-sm mb-8 leading-relaxed">
          The page you're looking for doesn't exist or has been moved.
          Let's get you back on track.
        </p>

        <div className="flex items-center justify-center gap-3">
          <Button
            variant="secondary"
            leftIcon={<ArrowLeft className="h-4 w-4" />}
            onClick={() => window.history.back()}
          >
            Go back
          </Button>
          <Link to="/dashboard">
            <Button leftIcon={<Home className="h-4 w-4" />}>
              Dashboard
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
