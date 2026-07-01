import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthLayout }           from './components/layout/AuthLayout'
import { AppLayout }            from './components/layout/AppLayout'
import { LoginPage }            from './pages/LoginPage'
import { RegisterPage }         from './pages/RegisterPage'
import { DashboardPage }        from './pages/DashboardPage'
import { HealthFormPage }       from './pages/HealthFormPage'
import { RecommendationsPage }  from './pages/RecommendationsPage'
import { ProfilePage }          from './pages/ProfilePage'
import { NotFoundPage }         from './pages/NotFoundPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>

        {/* ── Public / Auth routes ────────────────────────────── */}
        <Route element={<AuthLayout />}>
          <Route path="/login"    element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>

        {/* ── Protected / App routes ──────────────────────────── */}
        <Route element={<AppLayout />}>
          <Route path="/dashboard"       element={<DashboardPage />} />
          <Route path="/health-form"     element={<HealthFormPage />} />
          <Route path="/recommendations" element={<RecommendationsPage />} />
          <Route path="/profile"         element={<ProfilePage />} />
        </Route>

        {/* ── Root redirect ───────────────────────────────────── */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />

        {/* ── 404 ─────────────────────────────────────────────── */}
        <Route path="*" element={<NotFoundPage />} />

      </Routes>
    </BrowserRouter>
  )
}
