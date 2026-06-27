import { Outlet, Navigate } from 'react-router-dom'
import { Heart } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'

export function AuthLayout() {
  const { isAuthenticated } = useAuthStore()

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-teal-50/30 flex">
      {/* Left branding panel */}
      <div className="hidden lg:flex lg:w-[42%] bg-gradient-to-br from-teal-700 to-teal-900 flex-col justify-between p-12 relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-10 right-10 w-64 h-64 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-20 left-10 w-48 h-48 bg-teal-300 rounded-full blur-3xl" />
        </div>

        <div className="relative">
          <div className="flex items-center gap-3 mb-12">
            <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur">
              <Heart className="h-5 w-5 text-white fill-white" />
            </div>
            <span className="text-white font-bold text-xl">VitalIQ</span>
          </div>

          <h1 className="text-4xl font-bold text-white leading-tight mb-4">
            Your Personal<br />Health Coach
          </h1>
          <p className="text-teal-200 text-lg leading-relaxed">
            Track sleep, activity, nutrition, and stress. Get AI-powered insights personalised to your body.
          </p>
        </div>

        {/* Feature bullets */}
        <div className="relative space-y-4">
          {[
            { icon: '😴', text: 'Sleep quality analysis & coaching' },
            { icon: '🏃', text: 'Activity tracking & fitness goals' },
            { icon: '💧', text: 'Hydration & nutrition monitoring' },
            { icon: '🧘', text: 'Stress reduction personalised plans' },
          ].map((f) => (
            <div key={f.text} className="flex items-center gap-3">
              <span className="text-xl">{f.icon}</span>
              <p className="text-teal-100 text-sm">{f.text}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <div className="w-8 h-8 bg-health-green rounded-lg flex items-center justify-center">
              <Heart className="h-4 w-4 text-white fill-white" />
            </div>
            <span className="font-bold text-health-slate">VitalIQ</span>
          </div>
          <Outlet />
        </div>
      </div>
    </div>
  )
}
