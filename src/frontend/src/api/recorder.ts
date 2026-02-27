import { api } from './index'

export interface RecorderStatus {
  recording: boolean
  paused: boolean
  event_count: number
}

export interface RecorderStopResult {
  steps: any[]
  count: number
}

export const recorderApi = {
  start: () => api.post<{ status: string }>('/recorder/start'),
  stop: () => api.post<RecorderStopResult>('/recorder/stop'),
  pause: () => api.post<{ status: string }>('/recorder/pause'),
  getStatus: () => api.get<RecorderStatus>('/recorder/status'),
}
