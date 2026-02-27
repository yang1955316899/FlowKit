<template>
  <div class="recorder-view">
    <div class="recorder-header">
      <h1>录制器</h1>
      <p class="subtitle">录制键盘和鼠标操作，自动生成流程步骤</p>
    </div>

    <div class="recorder-controls">
      <button
        v-if="!status.recording"
        @click="startRecording"
        class="btn btn-primary btn-large"
      >
        <span class="icon">⏺</span>
        开始录制
      </button>

      <template v-else>
        <button @click="pauseRecording" class="btn btn-secondary">
          <span class="icon">{{ status.paused ? '▶' : '⏸' }}</span>
          {{ status.paused ? '继续' : '暂停' }}
        </button>
        <button @click="stopRecording" class="btn btn-danger">
          <span class="icon">⏹</span>
          停止录制
        </button>
      </template>

      <div v-if="status.recording" class="recording-indicator">
        <span class="pulse-dot"></span>
        <span class="text">
          {{ status.paused ? '已暂停' : '录制中' }} - {{ status.event_count }} 个事件
        </span>
      </div>
    </div>

    <div v-if="steps.length > 0" class="steps-preview">
      <div class="steps-header">
        <h2>录制的步骤 ({{ steps.length }})</h2>
        <button @click="saveAsFlow" class="btn btn-success">
          <span class="icon">💾</span>
          保存为流程
        </button>
      </div>

      <div class="steps-list">
        <div
          v-for="(step, index) in steps"
          :key="index"
          class="step-item"
        >
          <div class="step-index">{{ index + 1 }}</div>
          <div class="step-icon">{{ getStepIcon(step.type) }}</div>
          <div class="step-content">
            <div class="step-type">{{ getStepName(step.type) }}</div>
            <div class="step-details">{{ getStepSummary(step) }}</div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="!status.recording" class="empty-state">
      <div class="empty-icon">🎬</div>
      <p>点击"开始录制"按钮开始录制操作</p>
      <p class="hint">录制完成后，步骤将显示在这里</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { recorderApi, type RecorderStatus } from '@/api/recorder'
import { useRouter } from 'vue-router'

const router = useRouter()

const status = ref<RecorderStatus>({
  recording: false,
  paused: false,
  event_count: 0,
})

const steps = ref<any[]>([])
let pollInterval: number | null = null

const startRecording = async () => {
  try {
    await recorderApi.start()
    startPolling()
  } catch (error) {
    console.error('Failed to start recording:', error)
  }
}

const pauseRecording = async () => {
  try {
    await recorderApi.pause()
    await updateStatus()
  } catch (error) {
    console.error('Failed to pause recording:', error)
  }
}

const stopRecording = async () => {
  try {
    const result = await recorderApi.stop()
    steps.value = result.steps
    stopPolling()
    await updateStatus()
  } catch (error) {
    console.error('Failed to stop recording:', error)
  }
}

const updateStatus = async () => {
  try {
    const newStatus = await recorderApi.getStatus()
    status.value = newStatus
  } catch (error) {
    console.error('Failed to get status:', error)
  }
}

const startPolling = () => {
  if (pollInterval) return
  pollInterval = window.setInterval(updateStatus, 500)
}

const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

const saveAsFlow = () => {
  // Navigate to flow editor with recorded steps
  router.push({
    name: 'FlowEditor',
    query: { steps: JSON.stringify(steps.value) }
  })
}

const getStepIcon = (type: string): string => {
  const icons: Record<string, string> = {
    delay: '⏱',
    keys: '⌨',
    mouse_click: '🖱',
    mouse_move: '↗',
    mouse_scroll: '🔄',
  }
  return icons[type] || '▸'
}

const getStepName = (type: string): string => {
  const names: Record<string, string> = {
    delay: '延迟',
    keys: '按键',
    mouse_click: '鼠标点击',
    mouse_move: '鼠标移动',
    mouse_scroll: '鼠标滚轮',
  }
  return names[type] || type
}

const getStepSummary = (step: any): string => {
  const { type } = step
  if (type === 'delay') {
    return `${step.ms}ms`
  } else if (type === 'keys') {
    return step.target || step.label || ''
  } else if (type === 'mouse_click') {
    return `(${step.x}, ${step.y}) ${step.button || ''}`
  } else if (type === 'mouse_move') {
    return `(${step.x}, ${step.y})`
  } else if (type === 'mouse_scroll') {
    return `delta=${step.delta}`
  }
  return ''
}

onMounted(() => {
  updateStatus()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.recorder-view {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.recorder-header {
  margin-bottom: 32px;
}

.recorder-header h1 {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 8px;
}

.subtitle {
  color: var(--color-text-secondary);
  font-size: 14px;
}

.recorder-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
  padding: 24px;
  background: var(--color-card);
  border-radius: 12px;
  border: 1px solid var(--color-border);
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn-large {
  padding: 14px 28px;
  font-size: 16px;
}

.btn-primary {
  background: var(--color-accent);
  color: white;
}

.btn-primary:hover {
  background: var(--color-accent-hover);
}

.btn-secondary {
  background: var(--color-bg-secondary);
  color: var(--color-text);
}

.btn-secondary:hover {
  background: var(--color-bg-tertiary);
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover {
  background: #dc2626;
}

.btn-success {
  background: #10b981;
  color: white;
}

.btn-success:hover {
  background: #059669;
}

.icon {
  font-size: 18px;
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
  padding: 8px 16px;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 8px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #ef4444;
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

.recording-indicator .text {
  font-size: 14px;
  font-weight: 500;
  color: #ef4444;
}

.steps-preview {
  background: var(--color-card);
  border-radius: 12px;
  border: 1px solid var(--color-border);
  overflow: hidden;
}

.steps-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border);
}

.steps-header h2 {
  font-size: 18px;
  font-weight: 600;
}

.steps-list {
  max-height: 500px;
  overflow-y: auto;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  border-bottom: 1px solid var(--color-border);
  transition: background 0.2s;
}

.step-item:hover {
  background: var(--color-bg-secondary);
}

.step-item:last-child {
  border-bottom: none;
}

.step-index {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-secondary);
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.step-icon {
  font-size: 20px;
}

.step-content {
  flex: 1;
}

.step-type {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
}

.step-details {
  font-size: 12px;
  color: var(--color-text-secondary);
  font-family: monospace;
}

.empty-state {
  text-align: center;
  padding: 80px 24px;
  color: var(--color-text-secondary);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-state p {
  margin: 8px 0;
}

.hint {
  font-size: 12px;
  opacity: 0.7;
}
</style>
