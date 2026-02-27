<template>
  <div class="titlebar" @mousedown="startDrag">
    <div class="titlebar-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="['tab-btn', { active: currentTab === tab.id }]"
        @click="switchTab(tab.id)"
        :title="tab.label"
      >
        {{ tab.icon }}
      </button>
    </div>
    <div class="titlebar-controls">
      <button class="ctrl-btn" @click="handleOpenSettings" title="设置">⚙️</button>
      <button class="ctrl-btn" @click="minimize" title="最小化">─</button>
      <button class="ctrl-btn close" @click="close" title="关闭">×</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { electronWindow, isElectron, openSettings } from '@/electron'

const router = useRouter()
const appStore = useAppStore()

const tabs = [
  { id: 'launcher', icon: '🚀', label: '启动器' },
  { id: 'dashboard', icon: '📈', label: '仪表盘' },
  { id: 'overview', icon: '🔑', label: '总览' },
]

const currentTab = computed(() => appStore.currentTab)

const switchTab = (tabId: string) => {
  appStore.setTab(tabId as any)
  router.push(`/${tabId}`)
}

const handleOpenSettings = () => {
  if (isElectron()) {
    // Electron: 打开新窗口
    openSettings()
  } else {
    // 浏览器: 显示 Dialog
    appStore.setShowSettings(true)
  }
}

const minimize = () => { if (isElectron()) electronWindow.minimize() }
const close = () => { if (isElectron()) electronWindow.close() }
const startDrag = () => { /* Electron frameless drag handled by CSS -webkit-app-region */ }
</script>

<style scoped>
.titlebar {
  height: 32px;
  min-height: 32px;
  background: var(--card);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
  border-bottom: 1px solid var(--border-subtle);
  -webkit-app-region: drag;
}

.titlebar-tabs {
  display: flex;
  gap: 2px;
  -webkit-app-region: no-drag;
}

.tab-btn {
  width: 30px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  font-size: 13px;
  transition: background 0.15s;
  opacity: 0.5;
}

.tab-btn:hover { background: var(--btn-hover); opacity: 0.8; }
.tab-btn.active { background: var(--accent-glow); opacity: 1; }

.titlebar-controls {
  display: flex;
  gap: 2px;
  -webkit-app-region: no-drag;
}

.ctrl-btn {
  width: 28px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  font-size: 14px;
  color: var(--dim);
  transition: all 0.15s;
}

.ctrl-btn:hover { background: var(--btn-hover); color: var(--text); }
.ctrl-btn.close:hover { background: var(--red); color: #fff; }
</style>
