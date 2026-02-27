<template>
  <div id="app">
    <!-- 只在主窗口路由显示 TitleBar -->
    <TitleBar v-if="isMainWindow" />

    <div class="app-content" :class="{ 'full-page': !isMainWindow }">
      <router-view v-slot="{ Component }">
        <transition name="tab-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>

    <Toast />
    <LoadingOverlay :show="loading" :message="loadingMessage" />

    <!-- 浏览器环境显示 Dialog（Element 风格） -->
    <template v-if="!isElectronEnv">
      <Dialog
        :show="appStore.showSettings"
        title="设置"
        width="800px"
        @close="appStore.setShowSettings(false)"
      >
        <Settings />
      </Dialog>

      <Dialog
        :show="appStore.showFlowEditor"
        title="流程编排器"
        width="1000px"
        @close="appStore.setShowFlowEditor(false)"
      >
        <FlowEditor />
      </Dialog>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import TitleBar from '@/components/layout/TitleBar.vue'
import Toast from '@/components/layout/Toast.vue'
import Dialog from '@/components/common/Dialog.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import Settings from '@/views/Settings/index.vue'
import FlowEditor from '@/views/FlowEditor/index.vue'
import { isElectron, getEnvironment } from '@/electron'
import { useAppStore } from '@/stores/app'
import { useLoading } from '@/composables/useLoading'
import { useNetworkStatus } from '@/composables/useNetworkStatus'

const route = useRoute()
const appStore = useAppStore()
const { loading, message: loadingMessage } = useLoading()
const { online } = useNetworkStatus()

const isElectronEnv = computed(() => isElectron())

// 判断是否是主窗口路由（launcher/dashboard/overview）
const isMainWindow = computed(() => {
  const mainRoutes = ['launcher', 'dashboard', 'overview']
  return mainRoutes.includes(route.name as string)
})

onMounted(() => {
  const env = getEnvironment()
  console.log('Environment:', env)

  if (env.isElectron) {
    console.log('Running in Electron - using native windows')
  } else {
    console.log('Running in browser - using Element-style dialogs')
  }

  // Apply saved theme
  document.documentElement.setAttribute('data-theme', appStore.theme)
})
</script>

<style scoped>
#app {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg);
  color: var(--text);
}

.app-content {
  flex: 1;
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
}

.app-content.full-page {
  height: 100vh;
}
</style>
