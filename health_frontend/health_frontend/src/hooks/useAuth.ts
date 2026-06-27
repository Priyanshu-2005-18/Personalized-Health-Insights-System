import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { authApi } from '../api/auth'
import type { LoginRequest, RegisterRequest } from '../types'
import { getApiError } from '../utils'

export function useAuth() {
  const { user, isAuthenticated, setAuth, clearAuth } = useAuthStore()
  const navigate = useNavigate()

  const login = useCallback(
    async (data: LoginRequest): Promise<void> => {
      const tokens = await authApi.login(data)
      const me = await authApi.getMe()
      setAuth(me, tokens.access_token, tokens.refresh_token)
      navigate('/dashboard')
    },
    [setAuth, navigate]
  )

  const register = useCallback(
    async (data: RegisterRequest): Promise<void> => {
      const tokens = await authApi.register(data)
      const me = await authApi.getMe()
      setAuth(me, tokens.access_token, tokens.refresh_token)
      navigate('/dashboard')
    },
    [setAuth, navigate]
  )

  const logout = useCallback(async () => {
    try {
      const rt = localStorage.getItem('refresh_token')
      if (rt) await authApi.logout(rt)
    } finally {
      clearAuth()
      navigate('/login')
    }
  }, [clearAuth, navigate])

  return { user, isAuthenticated, login, register, logout }
}
