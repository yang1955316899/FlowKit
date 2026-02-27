import { api } from './index'
import type { Action, ActionsResponse, SearchResult } from '@/types/action'

export const actionApi = {
  getAll: (page?: number) => {
    const query = page !== undefined ? `?page=${page}` : ''
    return api.get<ActionsResponse>(`/actions${query}`)
  },

  add: (action: Partial<Action>) =>
    api.post<{ index: number; id: string }>('/actions', action),

  update: (idx: number, data: Partial<Action>) =>
    api.put<void>(`/actions/${idx}`, data),

  delete: (idx: number) => api.delete<void>(`/actions/${idx}`),

  execute: (idx: number) => api.post<{ message: string }>(`/actions/${idx}/execute`),

  executeAction: (action: Action) => api.post<void>('/actions/execute', action),

  reorder: (from: number, to: number) =>
    api.post<void>('/actions/reorder', { from, to }),

  search: (query: string) => api.get<SearchResult[]>(`/search?q=${encodeURIComponent(query)}`)
}
