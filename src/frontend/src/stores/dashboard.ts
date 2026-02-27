import { defineStore } from 'pinia'
import { ref } from 'vue'
import { tokenApi } from '@/api/tokens'
import type { Token, TokenStats, TokenDetail } from '@/types/token'

export const useDashboardStore = defineStore('dashboard', () => {
  const tokens = ref<Token[]>([])
  const currentTokenIdx = ref(0)
  const stats = ref<TokenStats | null>(null)
  const details = ref<TokenDetail[]>([])
  const loading = ref(false)
  const autoRefresh = ref(true)
  const refreshInterval = ref<number | null>(null)

  const fetchTokens = async () => {
    try {
      tokens.value = await tokenApi.getAll()
    } catch (error) {
      console.error('Failed to fetch tokens:', error)
    }
  }

  const fetchStats = async (idx?: number) => {
    const tokenIdx = idx !== undefined ? idx : currentTokenIdx.value
    loading.value = true
    try {
      stats.value = await tokenApi.getStats(tokenIdx)
    } catch (error) {
      console.error('Failed to fetch stats:', error)
      stats.value = null
    } finally {
      loading.value = false
    }
  }

  const fetchDetails = async (idx?: number) => {
    const tokenIdx = idx !== undefined ? idx : currentTokenIdx.value
    try {
      details.value = await tokenApi.getDetails(tokenIdx)
    } catch (error) {
      console.error('Failed to fetch details:', error)
      details.value = []
    }
  }

  const selectToken = async (idx: number) => {
    currentTokenIdx.value = idx
    await Promise.all([fetchStats(idx), fetchDetails(idx)])
  }

  const startAutoRefresh = () => {
    if (refreshInterval.value) return
    refreshInterval.value = window.setInterval(() => {
      if (autoRefresh.value) {
        fetchStats()
        fetchDetails()
      }
    }, 20000) // 20 seconds
  }

  const stopAutoRefresh = () => {
    if (refreshInterval.value) {
      clearInterval(refreshInterval.value)
      refreshInterval.value = null
    }
  }

  return {
    tokens,
    currentTokenIdx,
    stats,
    details,
    loading,
    autoRefresh,
    fetchTokens,
    fetchStats,
    fetchDetails,
    selectToken,
    startAutoRefresh,
    stopAutoRefresh
  }
})
