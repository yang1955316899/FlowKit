import { api } from './index'
import type { FlowCategory, FlowExecuteRequest } from '@/types/flow'
import type { Page, Action } from '@/types/action'

export const flowApi = {
  getStepTypes: () => api.get<FlowCategory[]>('/flows/step-types'),

  execute: (data: FlowExecuteRequest) =>
    api.post<{ message: string }>('/flows/execute', data),

  getPages: () => api.get<Page[]>('/pages'),

  updatePageAction: (pageIdx: number, actionIdx: number, data: Partial<Action>) =>
    api.put<void>(`/pages/${pageIdx}/actions/${actionIdx}`, data)
}
