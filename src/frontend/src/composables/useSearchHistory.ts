/**
 * Search history management composable
 * Stores and retrieves recent search queries from localStorage
 */

import { ref, computed } from 'vue'
import { STORAGE_KEYS, TEXT_CONFIG } from '@/constants'

export function useSearchHistory() {
  const history = ref<string[]>([])

  // Load history from localStorage
  const loadHistory = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.SEARCH_HISTORY)
      if (stored) {
        history.value = JSON.parse(stored)
      }
    } catch (error) {
      console.error('Failed to load search history:', error)
      history.value = []
    }
  }

  // Save history to localStorage
  const saveHistory = () => {
    try {
      localStorage.setItem(STORAGE_KEYS.SEARCH_HISTORY, JSON.stringify(history.value))
    } catch (error) {
      console.error('Failed to save search history:', error)
    }
  }

  // Add a search query to history
  const addToHistory = (query: string) => {
    const trimmed = query.trim()
    if (!trimmed) return

    // Remove if already exists
    history.value = history.value.filter(item => item !== trimmed)

    // Add to beginning
    history.value.unshift(trimmed)

    // Keep only the most recent items
    if (history.value.length > TEXT_CONFIG.MAX_SEARCH_HISTORY) {
      history.value = history.value.slice(0, TEXT_CONFIG.MAX_SEARCH_HISTORY)
    }

    saveHistory()
  }

  // Remove a specific item from history
  const removeFromHistory = (query: string) => {
    history.value = history.value.filter(item => item !== query)
    saveHistory()
  }

  // Clear all history
  const clearHistory = () => {
    history.value = []
    saveHistory()
  }

  // Get filtered history based on current query
  const getFilteredHistory = (query: string) => {
    if (!query.trim()) {
      return history.value
    }

    const lowerQuery = query.toLowerCase()
    return history.value.filter(item =>
      item.toLowerCase().includes(lowerQuery)
    )
  }

  // Initialize
  loadHistory()

  return {
    history: computed(() => history.value),
    addToHistory,
    removeFromHistory,
    clearHistory,
    getFilteredHistory
  }
}
