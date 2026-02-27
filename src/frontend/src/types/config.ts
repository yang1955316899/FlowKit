import type { Page } from './action'

export interface AppConfig {
  window?: WindowConfig
  launcher?: LauncherConfig
  api?: ApiConfig
}

export interface WindowConfig {
  width?: number
  opacity?: number
  snap_threshold?: number
  animation_speed?: number
}

export interface LauncherConfig {
  current_page?: number
  pages?: Page[]
}

export interface ApiConfig {
  base_url?: string
  credential?: string
}
