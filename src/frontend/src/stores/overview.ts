import { defineStore } from 'pinia'
import { ref } from 'vue'
import { tokenApi } from '@/api/tokens'
import type { Token } from '@/types/token'

export const useOverviewStore = defineStore('overview', () => {
  const tokens = ref<Token[]>([])
  const loading = ref(false)
  const editingToken = ref<Token | null>(null)

  const fetchTokens = async () => {
    loading.value = true
    try {
      tokens.value = await tokenApi.getAll()
    } catch (error) {
      console.error('Failed to fetch tokens:', error)
    } finally {
      loading.value = false
    }
  }

  const addToken = async (data: { name: string; credential: string; daily_limit?: number }) => {
    try {
      await tokenApi.add(data)
      await fetchTokens()
    } catch (error) {
      console.error('Failed to add token:', error)
      throw error
    }
  }

  const updateToken = async (idx: number, data: Partial<Token>) => {
    try {
      await tokenApi.update(idx, data)
      await fetchTokens()
    } catch (error) {
      console.error('Failed to update token:', error)
      throw error
    }
  }

  const deleteToken = async (idx: number) => {
    try {
      await tokenApi.delete(idx)
      await fetchTokens()
    } catch (error) {
      console.error('Failed to delete token:', error)
      throw error
    }
  }

  const startEdit = (token: Token) => {
    editingToken.value = { ...token }
  }

  const cancelEdit = () => {
    editingToken.value = null
  }

  return {
    tokens,
    loading,
    editingToken,
    fetchTokens,
    addToken,
    updateToken,
    deleteToken,
    startEdit,
    cancelEdit
  }
})
