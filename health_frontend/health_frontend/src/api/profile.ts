import apiClient from './client'
import type { UserProfile } from '../types'

export const profileApi = {
  get: async (): Promise<UserProfile> => {
    const res = await apiClient.get<UserProfile>('/users/me/profile')
    return res.data
  },

  create: async (data: Partial<UserProfile>): Promise<UserProfile> => {
    const res = await apiClient.post<UserProfile>('/users/me/profile', data)
    return res.data
  },

  update: async (data: Partial<UserProfile>): Promise<UserProfile> => {
    const res = await apiClient.patch<UserProfile>('/users/me/profile', data)
    return res.data
  },
}
