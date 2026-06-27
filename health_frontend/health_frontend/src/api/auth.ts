import apiClient from './client'
import type { AuthTokens, LoginRequest, RegisterRequest, User } from '../types'

export const authApi = {
  login: async (data: LoginRequest): Promise<AuthTokens> => {
    const res = await apiClient.post<AuthTokens>('/auth/login', data)
    return res.data
  },

  register: async (data: RegisterRequest): Promise<AuthTokens> => {
    const res = await apiClient.post<AuthTokens>('/auth/register', data)
    return res.data
  },

  logout: async (refresh_token: string): Promise<void> => {
    await apiClient.post('/auth/logout', { refresh_token })
  },

  getMe: async (): Promise<User> => {
    const res = await apiClient.get<User>('/users/me')
    return res.data
  },

  verifyToken: async (): Promise<{ message: string }> => {
    const res = await apiClient.get('/users/me')
    return res.data
  },
}
