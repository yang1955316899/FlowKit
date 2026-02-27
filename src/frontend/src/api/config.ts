import { api } from './index'
import type { AppConfig } from '@/types/config'

export const configApi = {
  get: () => api.get<AppConfig>('/config'),

  update: (data: Partial<AppConfig>) => api.put<void>('/config', data)
}
