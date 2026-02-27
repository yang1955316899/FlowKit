<template>
  <div class="script-editor-view">
    <div class="editor-header">
      <h1>脚本编辑器</h1>
      <div class="actions">
        <button @click="runScript" :disabled="running" class="btn btn-primary">
          <span class="icon">{{ running ? '⏳' : '▶' }}</span>
          {{ running ? '运行中...' : '运行' }}
        </button>
        <button @click="clearOutput" class="btn btn-secondary">
          <span class="icon">🗑</span>
          清空输出
        </button>
      </div>
    </div>

    <div class="editor-container">
      <div class="code-section">
        <div class="section-header">
          <h2>Python 代码</h2>
          <span class="hint">编写 Python 代码并点击运行</span>
        </div>
        <textarea
          v-model="code"
          class="code-editor"
          placeholder="# 输入 Python 代码
print('Hello, World!')

# 示例：获取系统信息
import platform
print(f'系统: {platform.system()}')
print(f'版本: {platform.version()}')"
          spellcheck="false"
        ></textarea>
      </div>

      <div class="output-section">
        <div class="section-header">
          <h2>输出</h2>
          <span v-if="lastRunTime" class="timestamp">
            最后运行: {{ lastRunTime }}
          </span>
        </div>
        <div class="output-panel" ref="outputPanel">
          <div v-if="!output.stdout && !output.stderr" class="empty-output">
            运行脚本后，输出将显示在这里
          </div>
          <div v-else>
            <div v-if="output.stdout" class="output-block stdout">
              <div class="output-label">标准输出:</div>
              <pre>{{ output.stdout }}</pre>
            </div>
            <div v-if="output.stderr" class="output-block stderr">
              <div class="output-label">错误输出:</div>
              <pre>{{ output.stderr }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { api } from '@/api'

const code = ref('')
const running = ref(false)
const output = ref<{ stdout: string; stderr: string; success: boolean }>({
  stdout: '',
  stderr: '',
  success: true,
})
const lastRunTime = ref('')
const outputPanel = ref<HTMLElement | null>(null)

const runScript = async () => {
  if (!code.value.trim()) {
    return
  }

  running.value = true
  output.value = { stdout: '', stderr: '', success: true }

  try {
    const result = await api.post<{
      stdout: string
      stderr: string
      success: boolean
    }>('/scripts/execute', {
      code: code.value,
    })

    output.value = result
    lastRunTime.value = new Date().toLocaleTimeString()

    // Scroll to bottom of output
    await nextTick()
    if (outputPanel.value) {
      outputPanel.value.scrollTop = outputPanel.value.scrollHeight
    }
  } catch (error) {
    output.value = {
      stdout: '',
      stderr: `执行失败: ${error}`,
      success: false,
    }
  } finally {
    running.value = false
  }
}

const clearOutput = () => {
  output.value = { stdout: '', stderr: '', success: true }
  lastRunTime.value = ''
}
</script>

<style scoped>
.script-editor-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
}

.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-card);
}

.editor-header h1 {
  font-size: 20px;
  font-weight: 600;
}

.actions {
  display: flex;
  gap: 12px;
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

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--color-accent);
  color: white;
}

.btn-primary:hover:not(:disabled) {
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

.editor-container {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  background: var(--color-border);
  overflow: hidden;
}

.code-section,
.output-section {
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-card);
}

.section-header h2 {
  font-size: 14px;
  font-weight: 600;
}

.hint,
.timestamp {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.code-editor {
  flex: 1;
  padding: 16px;
  border: none;
  background: var(--color-bg);
  color: var(--color-text);
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  resize: none;
  outline: none;
}

.code-editor::placeholder {
  color: var(--color-text-secondary);
  opacity: 0.5;
}

.output-panel {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.empty-output {
  color: var(--color-text-secondary);
  text-align: center;
  padding: 40px 20px;
}

.output-block {
  margin-bottom: 16px;
}

.output-block:last-child {
  margin-bottom: 0;
}

.output-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
  opacity: 0.7;
}

.stdout .output-label {
  color: #10b981;
}

.stderr .output-label {
  color: #ef4444;
}

.output-block pre {
  margin: 0;
  padding: 12px;
  background: var(--color-card);
  border-radius: 6px;
  border-left: 3px solid;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.stdout pre {
  border-left-color: #10b981;
}

.stderr pre {
  border-left-color: #ef4444;
  color: #ef4444;
}
</style>
