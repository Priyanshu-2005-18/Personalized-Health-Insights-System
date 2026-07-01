import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { Menu, X, Heart, LayoutDashboard, ClipboardList, Lightbulb, User, LogOut } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import { authApi } from '../../api/auth'
import { cn } from '../../utils'

const NAV = [
  { to: '/dashboard',       icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/health-form',     icon: ClipboardList,   label: 'Log Data' },
  { to: '/recommendations', icon: Lightbulb,       label: 'Recommendations' },
  { to: '/profile',         icon: User,            label: 'Profile' },
]

export function TopBar() {
  const [open, setOpen] = useState(false)
  const { user, clearAuth } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    try {
      const rt = localStorage.getItem('refresh_token')
      if (rt) await authApi.logout(rt)
    } finally {
      clearAuth()
      navigate('/login')
    }
  }

  return (
    <header className="lg:hidden sticky top-0 z-40 bg-white border-b border-health-border">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-health-green rounded-lg flex items-center justify-center">
            <Heart className="h-3.5 w-3.5 text-white fill-white" />
          </div>
          <span className="font-bold text-sm text-health-slate">VitalIQ</span>
        </div>
        <button onClick={() => setOpen(!open)} className="p-1.5 rounded-lg hover:bg-health-surface">
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {open && (
        <nav className="px-3 pb-3 border-t border-health-border space-y-0.5 animate-fade-up">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all',
                  isActive
                    ? 'bg-teal-50 text-health-green'
                    : 'text-health-muted hover:text-health-slate hover:bg-health-surface'
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className={cn('h-4 w-4', isActive ? 'text-health-green' : 'text-health-muted')} />
                  {label}
                </>
              )}
            </NavLink>
          ))}
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2.5 text-sm font-medium text-health-muted hover:text-red-600 hover:bg-red-50 rounded-xl transition-all"
          >
            <LogOut className="h-4 w-4" /> Sign out
          </button>
        </nav>
      )}
    </header>
  )
}
