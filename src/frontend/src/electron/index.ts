// Electron API 统一导出
export * from './window'
export * from './system'
export * from './python'

// 检测是否在 Electron 环境
export const isElectron = (): boolean => {
  return typeof window !== 'undefined' && typeof window.electronAPI !== 'undefined'
}

// 获取环境信息
export const getEnvironment = () => {
  if (isElectron() && window.electronAPI) {
    return {
      isElectron: true,
      isDev: window.electronAPI.isDev
    }
  }
  return {
    isElectron: false,
    isDev: false
  }
}

// 打开新窗口
export const openSettings = () => {
  if (isElectron() && window.electronAPI.openSettings) {
    window.electronAPI.openSettings()
  }
}

export const openFlowEditor = () => {
  if (isElectron() && window.electronAPI.openFlowEditor) {
    window.electronAPI.openFlowEditor()
  }
}

// TypeScript 类型声明
declare global {
  interface Window {
    electronAPI?: {
      minimizeWindow: () => void
      maximizeWindow: () => void
      closeWindow: () => void
      resizeCompact: () => void
      resizeNormal: () => void
      openSettings: () => void
      openFlowEditor: () => void
      executePython: (code: any) => Promise<any>
      showNotification: (title: string, body: string) => void
      onNavigate: (callback: (route: string) => void) => void
      isElectron: boolean
      isDev: boolean
    }
  }
}
