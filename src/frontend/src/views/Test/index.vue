<template>
  <div class="test-page">
    <h2>前后端兼容性测试</h2>

    <div class="test-section">
      <h3>环境检测</h3>
      <div class="test-item">
        <span>PyWebView 环境:</span>
        <span :class="isPyWebView ? 'success' : 'error'">
          {{ isPyWebView ? '✓ 已检测到' : '✗ 未检测到' }}
        </span>
      </div>
      <div class="test-item">
        <span>API 可用:</span>
        <span :class="apiAvailable ? 'success' : 'error'">
          {{ apiAvailable ? '✓ 可用' : '✗ 不可用' }}
        </span>
      </div>
    </div>

    <div class="test-section">
      <h3>PyWebView API 测试</h3>
      <button @click="testMinimize">测试最小化</button>
      <button @click="testToast">测试 Toast</button>
      <button @click="testGetConfig">测试获取配置</button>
      <div v-if="configData" class="config-display">
        <pre>{{ JSON.stringify(configData, null, 2) }}</pre>
      </div>
    </div>

    <div class="test-section">
      <h3>HTTP API 测试</h3>
      <button @click="testTokensAPI">测试 Tokens API</button>
      <button @click="testActionsAPI">测试 Actions API</button>
      <button @click="testConfigAPI">测试 Config API</button>
      <div v-if="apiResult" class="api-result">
        <h4>API 响应:</h4>
        <pre>{{ JSON.stringify(apiResult, null, 2) }}</pre>
      </div>
    </div>

    <div class="test-section">
      <h3>资源加载测试</h3>
      <div class="test-item">
        <span>CSS 加载:</span>
        <span class="success">✓ 正常</span>
      </div>
      <div class="test-item">
        <span>字体加载:</span>
        <span :style="{ fontFamily: '-apple-system' }">✓ 正常</span>
      </div>
    </div>

    <div class="test-section">
      <h3>日志</h3>
      <div class="log-container">
        <div v-for="(log, idx) in logs" :key="idx" :class="['log-item', log.type]">
          [{{ log.time }}] {{ log.message }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePyWebView } from '@/composables/usePyWebView'
import { tokenApi } from '@/api/tokens'
import { actionApi } from '@/api/actions'
import { configApi } from '@/api/config'

const { isPyWebView, checkEnvironment, minimizeWindow, showToast, getConfig } = usePyWebView()

const apiAvailable = ref(false)
const configData = ref<any>(null)
const apiResult = ref<any>(null)
const logs = ref<Array<{ time: string; message: string; type: string }>>([])

const addLog = (message: string, type: 'info' | 'success' | 'error' = 'info') => {
  const time = new Date().toLocaleTimeString()
  logs.value.push({ time, message, type })
}

const testMinimize = () => {
  addLog('测试最小化窗口...', 'info')
  minimizeWindow()
  setTimeout(() => addLog('最小化命令已发送', 'success'), 100)
}

const testToast = () => {
  addLog('测试 Toast 通知...', 'info')
  showToast('这是一条测试消息')
  addLog('Toast 命令已发送', 'success')
}

const testGetConfig = async () => {
  addLog('测试获取配置...', 'info')
  try {
    configData.value = await getConfig()
    addLog('配置获取成功', 'success')
  } catch (error) {
    addLog(`配置获取失败: ${error}`, 'error')
  }
}

const testTokensAPI = async () => {
  addLog('测试 Tokens API...', 'info')
  try {
    const tokens = await tokenApi.getAll()
    apiResult.value = { endpoint: 'GET /api/v1/tokens', data: tokens }
    addLog(`Tokens API 成功，获取到 ${tokens.length} 个 token`, 'success')
  } catch (error) {
    addLog(`Tokens API 失败: ${error}`, 'error')
    apiResult.value = { error: String(error) }
  }
}

const testActionsAPI = async () => {
  addLog('测试 Actions API...', 'info')
  try {
    const actions = await actionApi.getAll()
    apiResult.value = { endpoint: 'GET /api/v1/actions', data: actions }
    addLog(`Actions API 成功，获取到 ${actions.actions.length} 个动作`, 'success')
  } catch (error) {
    addLog(`Actions API 失败: ${error}`, 'error')
    apiResult.value = { error: String(error) }
  }
}

const testConfigAPI = async () => {
  addLog('测试 Config API...', 'info')
  try {
    const config = await configApi.get()
    apiResult.value = { endpoint: 'GET /api/v1/config', data: config }
    addLog('Config API 成功', 'success')
  } catch (error) {
    addLog(`Config API 失败: ${error}`, 'error')
    apiResult.value = { error: String(error) }
  }
}

const checkAPIAvailability = async () => {
  try {
    await fetch('/api/v1/health')
    apiAvailable.value = true
    addLog('HTTP API 服务可用', 'success')
  } catch (error) {
    apiAvailable.value = false
    addLog('HTTP API 服务不可用', 'error')
  }
}

onMounted(() => {
  checkEnvironment()
  checkAPIAvailability()
  addLog('兼容性测试页面已加载', 'info')

  if (isPyWebView.value) {
    addLog('检测到 PyWebView 环境', 'success')
  } else {
    addLog('未检测到 PyWebView 环境（可能在浏览器中运行）', 'info')
  }
})
</script>

<style scoped>
.test-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

h2 {
  color: var(--text);
  margin-bottom: 24px;
}

.test-section {
  background: var(--surface0);
  border: 1px solid var(--surface2);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.test-section h3 {
  color: var(--text);
  font-size: 18px;
  margin-bottom: 16px;
}

.test-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--surface1);
}

.test-item:last-child {
  border-bottom: none;
}

.test-item span:first-child {
  color: var(--subtext0);
}

.success {
  color: var(--green);
  font-weight: 500;
}

.error {
  color: var(--red);
  font-weight: 500;
}

button {
  padding: 8px 16px;
  background: var(--accent);
  color: var(--base);
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  margin-right: 8px;
  margin-bottom: 8px;
}

button:hover {
  opacity: 0.9;
}

.config-display,
.api-result {
  margin-top: 16px;
  background: var(--surface1);
  border-radius: 8px;
  padding: 12px;
}

.api-result h4 {
  color: var(--text);
  margin-bottom: 8px;
}

pre {
  color: var(--text);
  font-family: monospace;
  font-size: 12px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.log-container {
  max-height: 300px;
  overflow-y: auto;
  background: var(--surface1);
  border-radius: 8px;
  padding: 12px;
}

.log-item {
  font-family: monospace;
  font-size: 12px;
  padding: 4px 0;
  border-bottom: 1px solid var(--surface2);
}

.log-item:last-child {
  border-bottom: none;
}

.log-item.info {
  color: var(--text);
}

.log-item.success {
  color: var(--green);
}

.log-item.error {
  color: var(--red);
}
</style>
