import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, ClipboardList, Lightbulb,
  User, LogOut, Activity, Heart,
} from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import { authApi } from '../../api/auth'
import { cn } from '../../utils'

const NAV = [
  { to: '/dashboard',        icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/health-form',      icon: ClipboardList,   label: 'Log Health Data' },
  { to: '/recommendations',  icon: Lightbulb,       label: 'Recommendations' },
  { to: '/profile',          icon: User,            label: 'Profile' },
]

export function Sidebar() {
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
    <aside className="hidden lg:flex flex-col w-64 min-h-screen bg-white border-r border-health-border">

      {/* Logo */}
      <div className="flex items-center gap-2.5 px-6 py-5 border-b border-health-border">
        <div className="w-8 h-8 bg-health-green rounded-lg flex items-center justify-center">
          <Heart className="h-4 w-4 text-white fill-white" />
        </div>
        <div>
          <p className="font-bold text-health-slate text-sm leading-tight">VitalIQ</p>
          <p className="text-[10px] text-health-muted">Health Insights</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150',
                isActive
                  ? 'bg-teal-50 text-health-green'
                  : 'text-health-muted hover:text-health-slate hover:bg-health-surface'
              )
            }
          >
            {({ isActive }) => (
              <>
                <Icon className={cn('h-4 w-4 shrink-0', isActive ? 'text-health-green' : 'text-health-muted')} />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* User + logout */}
      <div className="px-3 pb-4 border-t border-health-border pt-4">
        <div className="flex items-center gap-3 px-3 py-2 mb-1">
          <div className="w-8 h-8 bg-teal-100 rounded-full flex items-center justify-center shrink-0">
            <span className="text-xs font-bold text-teal-700">
              {user?.username?.[0]?.toUpperCase() ?? 'U'}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-health-slate truncate">
              {user?.full_name ?? user?.username}
            </p>
            <p className="text-xs text-health-muted truncate">{user?.email}</p>
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="flex items-center gap-3 w-full px-3 py-2.5 text-sm font-medium text-health-muted hover:text-red-600 hover:bg-red-50 rounded-xl transition-all duration-150"
        >
          <LogOut className="h-4 w-4 shrink-0" />
          Sign out
        </button>
      </div>
    </aside>
  )
}
