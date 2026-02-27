import { ref } from 'vue'

interface PyWebViewAPI {
  js_minimize_window: () => void
  js_close_window: () => void
  js_show_toast: (message: string) => void
  js_get_config: () => any
  js_execute_action: (action: any) => any
}

declare global {
  interface Window {
    pywebview?: {
      api: PyWebViewAPI
    }
  }
}

export function usePyWebView() {
  const isPyWebView = ref(false)

  const checkEnvironment = () => {
    isPyWebView.value = typeof window.pywebview !== 'undefined'
    if (isPyWebView.value) {
      console.log('PyWebView environment detected')
    }
  }

  const minimizeWindow = () => {
    if (isPyWebView.value && window.pywebview?.api) {
      try {
        window.pywebview.api.js_minimize_window()
      } catch (error) {
        console.error('Failed to minimize window:', error)
      }
    }
  }

  const closeWindow = () => {
    if (isPyWebView.value && window.pywebview?.api) {
      try {
        window.pywebview.api.js_close_window()
      } catch (error) {
        console.error('Failed to close window:', error)
      }
    }
  }

  const showToast = (message: string) => {
    if (isPyWebView.value && window.pywebview?.api) {
      try {
        window.pywebview.api.js_show_toast(message)
      } catch (error) {
        console.error('Failed to show toast:', error)
      }
    }
  }

  const getConfig = async () => {
    if (isPyWebView.value && window.pywebview?.api) {
      try {
        return await window.pywebview.api.js_get_config()
      } catch (error) {
        console.error('Failed to get config:', error)
        return null
      }
    }
    return null
  }

  const executeAction = async (action: any) => {
    if (isPyWebView.value && window.pywebview?.api) {
      try {
        return await window.pywebview.api.js_execute_action(action)
      } catch (error) {
        console.error('Failed to execute action:', error)
        return null
      }
    }
    return null
  }

  return {
    isPyWebView,
    checkEnvironment,
    minimizeWindow,
    closeWindow,
    showToast,
    getConfig,
    executeAction
  }
}
