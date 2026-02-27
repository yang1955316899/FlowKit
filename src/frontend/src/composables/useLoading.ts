/**
 * Loading state management composable
 * Provides a centralized way to manage loading states across the application
 */

import { ref, computed } from 'vue'

export function useLoading() {
  const loading = ref(false)
  const message = ref<string>()

  const isLoading = computed(() => loading.value)

  const start = (msg?: string) => {
    loading.value = true
    message.value = msg
  }

  const stop = () => {
    loading.value = false
    message.value = undefined
  }

  /**
   * Wraps an async function with loading state management
   *
   * @param func - The async function to wrap
   * @param msg - Optional loading message
   * @returns The result of the function
   */
  const wrap = async <T>(func: () => Promise<T>, msg?: string): Promise<T> => {
    start(msg)
    try {
      return await func()
    } finally {
      stop()
    }
  }

  return {
    loading: isLoading,
    message: computed(() => message.value),
    start,
    stop,
    wrap
  }
}
