import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const currentTab = ref<'launcher' | 'dashboard' | 'overview'>('launcher')
  const theme = ref<'mocha' | 'latte'>('mocha')
  const showSettings = ref(false)
  const showFlowEditor = ref(false)

  const setTab = (tab: typeof currentTab.value) => {
    currentTab.value = tab
  }

  const setTheme = (newTheme: typeof theme.value) => {
    theme.value = newTheme
    document.documentElement.setAttribute('data-theme', newTheme)
  }

  const setShowSettings = (show: boolean) => {
    showSettings.value = show
  }

  const setShowFlowEditor = (show: boolean) => {
    showFlowEditor.value = show
  }

  return {
    currentTab,
    theme,
    showSettings,
    showFlowEditor,
    setTab,
    setTheme,
    setShowSettings,
    setShowFlowEditor
  }
})
