/**
 * Network status monitoring composable
 * Monitors online/offline status and provides network state information
 */

import { ref, onMounted, onUnmounted } from 'vue'
import { useToast } from './useToast'

export function useNetworkStatus() {
  const online = ref(navigator.onLine)
  const lastChecked = ref(new Date())
  const { warning, success } = useToast()

  const handleOnline = () => {
    online.value = true
    lastChecked.value = new Date()
    success('网络已连接')
  }

  const handleOffline = () => {
    online.value = false
    lastChecked.value = new Date()
    warning('网络已断开')
  }

  onMounted(() => {
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
  })

  onUnmounted(() => {
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
  })

  return {
    online,
    lastChecked
  }
}
