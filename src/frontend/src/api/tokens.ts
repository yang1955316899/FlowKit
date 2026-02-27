import { api } from './index'
import type { Token, TokenStats, TokenDetail } from '@/types/token'

export const tokenApi = {
  getAll: () => api.get<Token[]>('/tokens'),

  getStats: (idx: number) => api.get<TokenStats>(`/tokens/${idx}/stats`),

  getDetails: (idx: number) => api.get<TokenDetail[]>(`/tokens/${idx}/details`),

  add: (data: { name: string; credential: string; daily_limit?: number }) =>
    api.post<{ index: number }>('/tokens', data),

  update: (idx: number, data: Partial<Token>) =>
    api.put<void>(`/tokens/${idx}`, data),

  delete: (idx: number) => api.delete<void>(`/tokens/${idx}`)
}
