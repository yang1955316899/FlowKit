<template>
  <div v-if="visible" class="shell-output-modal" @click.self="close">
    <div class="modal-content">
      <div class="modal-header">
        <h2>{{ title }}</h2>
        <button @click="close" class="close-btn">✕</button>
      </div>

      <div class="output-container" ref="outputContainer">
        <pre v-if="output" class="output-text">{{ output }}</pre>
        <div v-else class="loading">
          <span class="spinner"></span>
          <span>执行中...</span>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="copyOutput" class="btn btn-secondary">
          <span class="icon">📋</span>
          复制输出
        </button>
        <button @click="close" class="btn btn-primary">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

interface Props {
  visible: boolean
  title: string
  output: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

const outputContainer = ref<HTMLElement | null>(null)

const close = () => {
  emit('close')
}

const copyOutput = () => {
  if (props.output) {
    navigator.clipboard.writeText(props.output)
  }
}

watch(
  () => props.output,
  async () => {
    await nextTick()
    if (outputContainer.value) {
      outputContainer.value.scrollTop = outputContainer.value.scrollHeight
    }
  }
)
</script>

<style scoped>
.shell-output-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  width: 90%;
  max-width: 800px;
  max-height: 80vh;
  background: var(--color-bg);
  border-radius: 12px;
  border: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-card);
}

.modal-header h2 {
  font-size: 16px;
  font-weight: 600;
}

.close-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 18px;
  color: var(--color-text-secondary);
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text);
}

.output-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.output-text {
  margin: 0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: var(--color-text);
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px;
  color: var(--color-text-secondary);
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--color-border);
  background: var(--color-card);
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
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

.icon {
  font-size: 16px;
}
</style>
