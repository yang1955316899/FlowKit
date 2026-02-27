import { defineStore } from 'pinia'
import { ref } from 'vue'
import { actionApi } from '@/api/actions'
import type { Action, ActionsResponse, SearchResult } from '@/types/action'
import { debounce } from '@/utils'
import { DELAY_CONFIG } from '@/constants'

export const useLauncherStore = defineStore('launcher', () => {
  const currentPage = ref(0)
  const pageName = ref('')
  const totalPages = ref(0)
  const actions = ref<Action[]>([])
  const loading = ref(false)
  const searchQuery = ref('')
  const searchResults = ref<SearchResult[]>([])

  const fetchActions = async (page?: number) => {
    loading.value = true
    try {
      const data = await actionApi.getAll(page)
      currentPage.value = data.page
      pageName.value = data.pageName
      totalPages.value = data.totalPages
      actions.value = data.actions
    } catch (error) {
      console.error('Failed to fetch actions:', error)
    } finally {
      loading.value = false
    }
  }

  const addAction = async (action: Partial<Action>) => {
    // 生成临时 ID
    const tempId = `temp-${Date.now()}`
    const tempAction: Action = {
      index: actions.value.length,
      id: tempId,
      type: action.type || 'app',
      label: action.label || '',
      icon: action.icon || '✦',
      hotkey: action.hotkey || '',
      steps: action.steps || [],
      delay: action.delay || 500
    }

    // 乐观更新：立即添加到列表
    actions.value.push(tempAction)

    try {
      const result = await actionApi.add(action)
      // 更新为服务器返回的真实数据
      const idx = actions.value.findIndex(a => a.id === tempId)
      if (idx !== -1) {
        actions.value[idx] = { ...tempAction, ...result }
      }
    } catch (error) {
      // 回滚：移除临时添加的项
      actions.value = actions.value.filter(a => a.id !== tempId)
      console.error('Failed to add action:', error)
      throw error
    }
  }

  const updateAction = async (idx: number, data: Partial<Action>) => {
    // 保存原始数据用于回滚
    const originalAction = { ...actions.value[idx] }

    // 乐观更新：立即更新 UI
    if (actions.value[idx]) {
      actions.value[idx] = { ...actions.value[idx], ...data }
    }

    try {
      await actionApi.update(idx, data)
    } catch (error) {
      // 回滚：恢复原始数据
      actions.value[idx] = originalAction
      console.error('Failed to update action:', error)
      throw error
    }
  }

  const deleteAction = async (idx: number) => {
    // 保存原始数据用于回滚
    const originalActions = [...actions.value]

    // 乐观更新：立即从列表移除
    actions.value = actions.value.filter((_, i) => i !== idx)

    try {
      await actionApi.delete(idx)
    } catch (error) {
      // 回滚：恢复原始列表
      actions.value = originalActions
      console.error('Failed to delete action:', error)
      throw error
    }
  }

  const executeAction = async (idx: number) => {
    try {
      await actionApi.execute(idx)
    } catch (error) {
      console.error('Failed to execute action:', error)
      throw error
    }
  }

  const reorderActions = async (from: number, to: number) => {
    // 保存原始顺序用于回滚
    const originalActions = [...actions.value]

    // 乐观更新：立即交换位置
    const temp = actions.value[from]
    actions.value[from] = actions.value[to]
    actions.value[to] = temp

    try {
      await actionApi.reorder(from, to)
    } catch (error) {
      // 回滚：恢复原始顺序
      actions.value = originalActions
      console.error('Failed to reorder actions:', error)
      throw error
    }
  }

  const searchInternal = async (query: string) => {
    if (!query.trim()) {
      searchResults.value = []
      return
    }
    try {
      searchResults.value = await actionApi.search(query)
    } catch (error) {
      console.error('Failed to search:', error)
      searchResults.value = []
    }
  }

  // Debounced search function
  const debouncedSearch = debounce(searchInternal, DELAY_CONFIG.DEBOUNCE_SEARCH)

  const search = (query: string) => {
    searchQuery.value = query
    debouncedSearch(query)
  }

  const clearSearch = () => {
    searchQuery.value = ''
    searchResults.value = []
  }

  return {
    currentPage,
    pageName,
    totalPages,
    actions,
    loading,
    searchQuery,
    searchResults,
    fetchActions,
    addAction,
    updateAction,
    deleteAction,
    executeAction,
    reorderActions,
    search,
    clearSearch
  }
})

