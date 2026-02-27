import { defineStore } from 'pinia'
import { ref } from 'vue'
import { flowApi } from '@/api/flows'
import type { FlowCategory, FlowExecuteRequest } from '@/types/flow'
import type { FlowStep } from '@/types/flow-steps'
import type { Page } from '@/types/action'

export const useFlowEditorStore = defineStore('flowEditor', () => {
  const stepTypes = ref<FlowCategory[]>([])
  const pages = ref<Page[]>([])
  const currentFlow = ref<FlowStep[] | null>(null)
  const loading = ref(false)

  const fetchStepTypes = async () => {
    try {
      stepTypes.value = await flowApi.getStepTypes()
    } catch (error) {
      console.error('Failed to fetch step types:', error)
    }
  }

  const fetchPages = async () => {
    try {
      pages.value = await flowApi.getPages()
    } catch (error) {
      console.error('Failed to fetch pages:', error)
    }
  }

  const executeFlow = async (data: FlowExecuteRequest) => {
    loading.value = true
    try {
      await flowApi.execute(data)
    } catch (error) {
      console.error('Failed to execute flow:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const saveToPage = async (pageIdx: number, actionIdx: number, steps: FlowStep[], delay: number) => {
    try {
      await flowApi.updatePageAction(pageIdx, actionIdx, { steps, delay })
    } catch (error) {
      console.error('Failed to save to page:', error)
      throw error
    }
  }

  return {
    stepTypes,
    pages,
    currentFlow,
    loading,
    fetchStepTypes,
    fetchPages,
    executeFlow,
    saveToPage
  }
})
