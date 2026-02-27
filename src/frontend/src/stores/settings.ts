import { defineStore } from 'pinia'
import { ref } from 'vue'
import { configApi } from '@/api/config'
import type { AppConfig } from '@/types/config'

export const useSettingsStore = defineStore('settings', () => {
  const config = ref<AppConfig>({})
  const loading = ref(false)

  const fetchConfig = async () => {
    loading.value = true
    try {
      config.value = await configApi.get()
    } catch (error) {
      console.error('Failed to fetch config:', error)
    } finally {
      loading.value = false
    }
  }

  const updateConfig = async (data: Partial<AppConfig>) => {
    try {
      await configApi.update(data)
      await fetchConfig()
    } catch (error) {
      console.error('Failed to update config:', error)
      throw error
    }
  }

  return {
    config,
    loading,
    fetchConfig,
    updateConfig
  }
})
