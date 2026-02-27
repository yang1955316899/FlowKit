import { ref } from 'vue'

export interface Toast {
  id: number
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
  duration: number
}

const toasts = ref<Toast[]>([])
let toastId = 0
const MAX_TOASTS = 3 // 最多同时显示 3 个 toast

export function useToast() {
  const show = (
    message: string,
    type: Toast['type'] = 'info',
    duration: number = 3000
  ) => {
    const id = toastId++
    const toast: Toast = { id, message, type, duration }

    // 限制数量：如果超过最大值，移除最旧的
    if (toasts.value.length >= MAX_TOASTS) {
      toasts.value.shift()
    }

    toasts.value.push(toast)

    if (duration > 0) {
      setTimeout(() => {
        remove(id)
      }, duration)
    }

    return id
  }

  const remove = (id: number) => {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index !== -1) {
      toasts.value.splice(index, 1)
    }
  }

  const success = (message: string, duration?: number) =>
    show(message, 'success', duration)

  const error = (message: string, duration?: number) =>
    show(message, 'error', duration)

  const warning = (message: string, duration?: number) =>
    show(message, 'warning', duration)

  const info = (message: string, duration?: number) =>
    show(message, 'info', duration)

  return {
    toasts,
    show,
    remove,
    success,
    error,
    warning,
    info
  }
}
