<template>
<div class="flow-editor-page">    <!-- 独立窗口标题栏 -->    <div class="page-header">      <span class="page-title">🔀 流程编排器</span>      <button class="close-btn" @click="closeWindow">×</button>    </div>
    <div class="flow-editor">
    <!-- 工具栏 -->
    <div class="toolbar">
      <button class="tb-btn" @click="clearCanvas">清空</button>
      <button class="tb-btn" @click="executeFlow">▶ 执行</button>
      <button class="tb-btn accent" @click="showSave = true" :disabled="flowSteps.length === 0">
        保存到页面
      </button>
    </div>

    <!-- 步骤面板 -->
    <div class="step-palette">
      <div v-for="cat in stepTypes" :key="cat.category" class="cat-group">
        <div class="cat-title">{{ cat.category }}</div>
        <div
          v-for="step in cat.steps"
          :key="step.type"
          class="step-item"
          @click="addStepToFlow(step)"
        >
          <span class="s-icon">{{ step.icon }}</span>
          <span class="s-name">{{ step.name }}</span>
        </div>
      </div>
    </div>

    <!-- 流程步骤列表 -->
    <div class="flow-steps">
      <div class="steps-header">
        <span class="steps-title">流程步骤 ({{ flowSteps.length }})</span>
        <span class="steps-delay">延迟: {{ flowDelay }}ms</span>
      </div>
      <div v-if="flowSteps.length === 0" class="steps-empty">
        点击上方步骤添加到流程
      </div>
      <div v-else class="steps-list">
        <div
          v-for="(step, idx) in flowSteps"
          :key="idx"
          class="flow-step-item"
        >
          <span class="step-num">{{ idx + 1 }}</span>
          <span class="step-icon">{{ getStepIcon(step.type) }}</span>
          <span class="step-type">{{ step.type }}</span>
          <button class="step-del" @click="removeStep(idx)">×</button>
        </div>
      </div>
      <div class="delay-control">
        <label>步骤间延迟 (ms)</label>
        <input v-model.number="flowDelay" type="number" min="0" step="100" />
      </div>
    </div>

    <!-- 保存弹窗 -->
    <PageSelector
      :show="showSave"
      :pages="pages"
      @close="showSave = false"
      @save="handleSaveToPage"
    />
  </div>
</div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useFlowEditorStore } from '@/stores/flowEditor'
import { useLauncherStore } from '@/stores/launcher'
import { useToast } from '@/composables/useToast'
import type { FlowStepType } from '@/types/flow'
import type { FlowStep } from '@/types/flow-steps'
import { FLOW_STEP_DEFAULTS } from '@/constants'
import PageSelector from './PageSelector.vue'

const router = useRouter()
const store = useFlowEditorStore()
const launcherStore = useLauncherStore()
const { success, error } = useToast()

const showSave = ref(false)
const flowSteps = ref<FlowStep[]>([])
const flowDelay = ref(FLOW_STEP_DEFAULTS.DELAY_DURATION)

const stepTypes = computed(() => store.stepTypes)
const pages = computed(() => store.pages)

const getStepIcon = (type: string) => {
  for (const cat of stepTypes.value) {
    const step = cat.steps.find(s => s.type === type)
    if (step) return step.icon
  }
  return '•'
}

const addStepToFlow = (stepType: FlowStepType) => {
  let step: FlowStep

  // Add default parameters based on step type
  switch (stepType.type) {
    case 'delay':
      step = { type: 'delay', duration: FLOW_STEP_DEFAULTS.DELAY_DURATION }
      break
    case 'keys':
      step = { type: 'keys', keys: 'ctrl+c' }
      break
    case 'type_text':
      step = { type: 'type_text', text: 'Hello', interval: FLOW_STEP_DEFAULTS.TYPE_TEXT_INTERVAL }
      break
    case 'app':
      step = { type: 'app', path: '' }
      break
    case 'shell':
      step = { type: 'shell', command: '' }
      break
    case 'url':
      step = { type: 'url', url: '' }
      break
    case 'snippet':
      step = { type: 'snippet', content: '' }
      break
    case 'toast':
      step = { type: 'toast', message: '', level: FLOW_STEP_DEFAULTS.TOAST_LEVEL, duration: FLOW_STEP_DEFAULTS.TOAST_DURATION }
      break
    case 'mouse_click':
      step = { type: 'mouse_click', x: 0, y: 0, button: FLOW_STEP_DEFAULTS.MOUSE_CLICK_BUTTON, clicks: FLOW_STEP_DEFAULTS.MOUSE_CLICK_COUNT }
      break
    case 'mouse_move':
      step = { type: 'mouse_move', x: 0, y: 0, duration: FLOW_STEP_DEFAULTS.MOUSE_MOVE_DURATION }
      break
    case 'set_var':
      step = { type: 'set_var', name: 'var', value: '' }
      break
    case 'http_request':
      step = { type: 'http_request', method: 'GET', url: '', timeout: FLOW_STEP_DEFAULTS.HTTP_TIMEOUT }
      break
    default:
      // Fallback for unknown types
      return
  }

  flowSteps.value.push(step)
}

const removeStep = (idx: number) => {
  flowSteps.value.splice(idx, 1)
}

const clearCanvas = () => {
  if (flowSteps.value.length > 0) {
    if (confirm('确定清空所有步骤？')) {
      flowSteps.value = []
    }
  }
}

const executeFlow = async () => {
  if (flowSteps.value.length === 0) {
    error('请先添加步骤')
    return
  }

  try {
    await store.executeFlow({ steps: flowSteps.value, delay: flowDelay.value })
    success('流程已执行')
  } catch {
    error('执行失败')
  }
}

const handleSaveToPage = async (pageIdx: number, actionIdx: number, label: string, icon: string) => {
  try {
    // Create a combo action with the flow steps
    await launcherStore.addAction({
      type: 'combo',
      label,
      icon,
      steps: flowSteps.value,
      delay: flowDelay.value
    })

    success('已保存到页面')
    showSave.value = false

    // Navigate to launcher
    router.push('/launcher')
  } catch {
    error('保存失败')
  }
}

onMounted(() => {
  store.fetchStepTypes()
  store.fetchPages()
})
const closeWindow = () => {  if (window.electronAPI?.closeWindow) {    window.electronAPI.closeWindow()  } else {    window.close()  }}
</script>

<style scoped>
.flow-editor-page {  display: flex;  flex-direction: column;  height: 100vh;  background: var(--bg);}.page-header {  display: flex;  align-items: center;  justify-content: space-between;  padding: 12px 16px;  border-bottom: 1px solid var(--border-subtle);  background: var(--card);}.page-title {  font-size: 14px;  font-weight: 600;}.close-btn {  width: 28px;  height: 28px;  border-radius: 6px;  font-size: 20px;  color: var(--dim);  transition: all 0.15s;}.close-btn:hover {  background: var(--btn-hover);  color: var(--text);}
.flow-editor {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 6px 10px;
  overflow: hidden;
}

.toolbar {
  display: flex;
  gap: 4px;
  margin-bottom: 6px;
}

.tb-btn {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  background: var(--card);
  color: var(--text);
  transition: background 0.15s;
}
.tb-btn:hover { background: var(--btn-hover); }
.tb-btn.accent { background: var(--accent-glow); color: var(--accent); }

.step-palette {
  max-height: 200px;
  overflow-y: auto;
  margin-bottom: 6px;
}

.cat-group { margin-bottom: 4px; }
.cat-title { font-size: 10px; color: var(--dim); margin: 4px 0 2px; }

.step-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  background: var(--card);
  border-radius: 6px;
  margin-bottom: 2px;
  cursor: pointer;
  font-size: 11px;
  transition: background 0.15s;
}
.step-item:hover { background: var(--btn-hover); }
.s-icon { font-size: 13px; }

.flow-steps {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--card);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 8px;
  min-height: 150px;
}

.steps-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border-subtle);
}

.steps-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--text);
}

.steps-delay {
  font-size: 10px;
  color: var(--dim);
  font-family: var(--mono);
}

.steps-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--dim);
  font-size: 11px;
}

.steps-list {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 8px;
}

.flow-step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: var(--card2);
  border-radius: 6px;
  margin-bottom: 4px;
  font-size: 11px;
}

.step-num {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-glow);
  color: var(--accent);
  border-radius: 50%;
  font-size: 9px;
  font-family: var(--mono);
  font-weight: 600;
}

.step-icon {
  font-size: 14px;
}

.step-type {
  flex: 1;
  color: var(--sub);
}

.step-del {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  font-size: 16px;
  color: var(--dim);
  transition: all 0.15s;
}

.step-del:hover {
  background: var(--red-glow);
  color: var(--red);
}

.delay-control {
  padding-top: 8px;
  border-top: 1px solid var(--border-subtle);
}

.delay-control label {
  display: block;
  font-size: 10px;
  color: var(--dim);
  margin-bottom: 4px;
}

.delay-control input {
  width: 100%;
  padding: 4px 8px;
  font-size: 11px;
  background: var(--card2);
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
  color: var(--text);
  font-family: var(--mono);
}
</div>
</style>
