<template>
  <div class="settings-page">
    <!-- 独立窗口标题栏 -->
    <div class="page-header">
      <span class="page-title">⚙️ 设置</span>
      <button class="close-btn" @click="closeWindow">×</button>
    </div>

    <div class="settings">
      <!-- 窗口 -->
      <div class="section-title">窗口</div>
    <div class="setting-row" @click="showOpacityEditor = !showOpacityEditor">
      <span class="row-label">透明度</span>
      <span class="row-value">{{ config.opacity }}</span>
    </div>
    <div v-if="showOpacityEditor" class="inline-editor">
      <input
        v-model.number="tempOpacity"
        type="range"
        min="0.1"
        max="1.0"
        step="0.01"
        class="slider"
      />
      <span class="slider-value">{{ tempOpacity.toFixed(2) }}</span>
      <button class="btn-save" @click="saveOpacity">✓</button>
      <button class="btn-cancel" @click="showOpacityEditor = false">✕</button>
    </div>

    <div class="setting-row" @click="showWidthEditor = !showWidthEditor">
      <span class="row-label">宽度</span>
      <span class="row-value">{{ config.width }}px</span>
    </div>
    <div v-if="showWidthEditor" class="inline-editor">
      <input
        v-model.number="tempWidth"
        type="range"
        min="200"
        max="800"
        step="10"
        class="slider"
      />
      <span class="slider-value">{{ tempWidth }}px</span>
      <button class="btn-save" @click="saveWidth">✓</button>
      <button class="btn-cancel" @click="showWidthEditor = false">✕</button>
    </div>

    <!-- 启动器 -->
    <div class="section-title">启动器</div>
    <div class="setting-row" @click="showGridEditor = !showGridEditor">
      <span class="row-label">网格</span>
      <span class="row-value">{{ config.gridCols }} x {{ config.gridRows }}</span>
    </div>
    <div v-if="showGridEditor" class="inline-editor grid-editor">
      <div class="grid-input">
        <label>列</label>
        <input v-model.number="tempGridCols" type="number" min="2" max="8" />
      </div>
      <div class="grid-input">
        <label>行</label>
        <input v-model.number="tempGridRows" type="number" min="2" max="10" />
      </div>
      <button class="btn-save" @click="saveGrid">✓</button>
      <button class="btn-cancel" @click="showGridEditor = false">✕</button>
    </div>

    <div class="setting-row" @click="showHotkeyEditor = !showHotkeyEditor">
      <span class="row-label">热键</span>
      <span class="row-value">{{ config.hotkey }}</span>
    </div>
    <div v-if="showHotkeyEditor" class="inline-editor">
      <input
        v-model="tempHotkey"
        type="text"
        placeholder="例如: ctrl+space"
        class="text-input"
        @keydown="recordHotkey"
      />
      <button class="btn-save" @click="saveHotkey">✓</button>
      <button class="btn-cancel" @click="showHotkeyEditor = false">✕</button>
    </div>

    <div class="setting-row" @click="toggleMiddleClick">
      <span class="row-label">鼠标中键</span>
      <div :class="['toggle', { on: config.middleClick }]">
        <div class="toggle-knob" />
      </div>
    </div>
    <div class="setting-row" @click="toggleSelectionPopup">
      <span class="row-label">选中浮窗</span>
      <div :class="['toggle', { on: config.selectionPopup }]">
        <div class="toggle-knob" />
      </div>
    </div>

    <!-- 主题 -->
    <div class="section-title">主题</div>
    <div
      v-for="t in themes"
      :key="t.id"
      :class="['radio-row', { active: config.theme === t.id }]"
      @click="setTheme(t.id)"
    >
      <span :class="['radio-dot', { checked: config.theme === t.id }]" />
      <span class="radio-label">{{ t.label }}</span>
    </div>

    <!-- 默认视图 -->
    <div class="section-title">默认视图</div>
    <div
      v-for="v in views"
      :key="v.id"
      :class="['radio-row', { active: config.defaultView === v.id }]"
      @click="setDefaultView(v.id)"
    >
      <span :class="['radio-dot', { checked: config.defaultView === v.id }]" />
      <span class="radio-label">{{ v.label }}</span>
    </div>

    <!-- 使用统计 -->
    <div class="section-title">使用统计</div>
    <div class="setting-row">
      <span class="row-label">总执行次数</span>
      <span class="row-value">{{ stats.total }}</span>
    </div>
    <div v-for="item in stats.top" :key="item.id" class="stat-row">
      <span class="stat-label">{{ item.icon }} {{ item.label }}</span>
      <span class="stat-ago">{{ item.ago }}</span>
      <span class="stat-count">{{ item.count }}次</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useAppStore } from '@/stores/app'
import { useSettingsStore } from '@/stores/settings'
import { debounce } from '@/composables/useDebounce'

const appStore = useAppStore()
const settingsStore = useSettingsStore()

const themes = [
  { id: 'dark', label: '深色' },
  { id: 'light', label: '浅色' },
]

const views = [
  { id: 'launcher', label: '启动器' },
  { id: 'detail', label: '详情' },
  { id: 'overview', label: '总览' },
]

const config = reactive({
  opacity: 0.92,
  width: 360,
  gridCols: 4,
  gridRows: 7,
  hotkey: 'ctrl+space',
  middleClick: true,
  selectionPopup: false,
  theme: 'dark',
  defaultView: 'launcher',
})

const stats = reactive({
  total: 0,
  top: [] as any[],
})

// 编辑器显示状态
const showOpacityEditor = ref(false)
const showWidthEditor = ref(false)
const showGridEditor = ref(false)
const showHotkeyEditor = ref(false)

// 临时编辑值
const tempOpacity = ref(0.92)
const tempWidth = ref(360)
const tempGridCols = ref(4)
const tempGridRows = ref(7)
const tempHotkey = ref('ctrl+space')

// 防抖保存函数
const debouncedSaveOpacity = debounce(async (value: number) => {
  if (value >= 0.1 && value <= 1.0) {
    config.opacity = value
    await settingsStore.updateConfig({ window: { opacity: value } })
  }
}, 500)

const debouncedSaveWidth = debounce(async (value: number) => {
  if (value >= 200 && value <= 800) {
    config.width = value
    await settingsStore.updateConfig({ window: { width: value } })
  }
}, 500)

// 监听滑块变化，自动保存
watch(tempOpacity, (newValue) => {
  if (showOpacityEditor.value) {
    debouncedSaveOpacity(newValue)
  }
})

watch(tempWidth, (newValue) => {
  if (showWidthEditor.value) {
    debouncedSaveWidth(newValue)
  }
})

const fetchConfig = async () => {
  await settingsStore.fetchConfig()
  const c = settingsStore.config
  if (c) {
    config.opacity = c.window?.opacity ?? 0.92
    config.width = c.window?.width ?? 360
    config.gridCols = c.launcher?.grid?.[0] ?? 4
    config.gridRows = c.launcher?.grid?.[1] ?? 7
    config.hotkey = c.launcher?.hotkey ?? 'ctrl+space'
    config.middleClick = c.launcher?.middle_click ?? true
    config.selectionPopup = c.launcher?.selection_popup ?? false
    config.theme = c.window?.theme ?? 'dark'
    config.defaultView = c.launcher?.default_view ?? 'launcher'
  }
}

const setTheme = async (id: string) => {
  config.theme = id
  appStore.setTheme(id === 'light' ? 'latte' : 'mocha')
  await settingsStore.updateConfig({ window: { theme: id } })
}

const setDefaultView = async (id: string) => {
  config.defaultView = id
  await settingsStore.updateConfig({ launcher: { default_view: id } })
}

const toggleMiddleClick = async () => {
  config.middleClick = !config.middleClick
  await settingsStore.updateConfig({ launcher: { middle_click: config.middleClick } })
}

const toggleSelectionPopup = async () => {
  config.selectionPopup = !config.selectionPopup
  await settingsStore.updateConfig({ launcher: { selection_popup: config.selectionPopup } })
}

const saveOpacity = async () => {
  if (tempOpacity.value >= 0.1 && tempOpacity.value <= 1.0) {
    config.opacity = tempOpacity.value
    await settingsStore.updateConfig({ window: { opacity: tempOpacity.value } })
    showOpacityEditor.value = false
  }
}

const saveWidth = async () => {
  if (tempWidth.value >= 200 && tempWidth.value <= 800) {
    config.width = tempWidth.value
    await settingsStore.updateConfig({ window: { width: tempWidth.value } })
    showWidthEditor.value = false
  }
}

const saveGrid = async () => {
  if (tempGridCols.value >= 2 && tempGridCols.value <= 8 &&
      tempGridRows.value >= 2 && tempGridRows.value <= 10) {
    config.gridCols = tempGridCols.value
    config.gridRows = tempGridRows.value
    await settingsStore.updateConfig({ launcher: { grid: [tempGridCols.value, tempGridRows.value] } })
    showGridEditor.value = false
  }
}

const saveHotkey = async () => {
  if (tempHotkey.value.trim()) {
    config.hotkey = tempHotkey.value
    await settingsStore.updateConfig({ launcher: { hotkey: tempHotkey.value } })
    showHotkeyEditor.value = false
  }
}

const recordHotkey = (e: KeyboardEvent) => {
  e.preventDefault()
  const keys: string[] = []
  if (e.ctrlKey) keys.push('ctrl')
  if (e.shiftKey) keys.push('shift')
  if (e.altKey) keys.push('alt')
  if (e.metaKey) keys.push('meta')

  const key = e.key.toLowerCase()
  if (!['control', 'shift', 'alt', 'meta'].includes(key)) {
    keys.push(key)
  }

  if (keys.length > 0) {
    tempHotkey.value = keys.join('+')
  }
}


const closeWindow = () => {
  if (window.electronAPI?.closeWindow) {
    window.electronAPI.closeWindow()
  } else {
    window.close()
  }
}
onMounted(() => {
  fetchConfig()
  // 初始化临时值
  tempOpacity.value = config.opacity
  tempWidth.value = config.width
  tempGridCols.value = config.gridCols
  tempGridRows.value = config.gridRows
  tempHotkey.value = config.hotkey
})
</script>

<style scoped>
.settings-page {  display: flex;  flex-direction: column;  height: 100vh;  background: var(--bg);}.page-header {  display: flex;  align-items: center;  justify-content: space-between;  padding: 12px 16px;  border-bottom: 1px solid var(--border-subtle);  background: var(--card);}.page-title {  font-size: 14px;  font-weight: 600;}.close-btn {  width: 28px;  height: 28px;  border-radius: 6px;  font-size: 20px;  color: var(--dim);  transition: all 0.15s;}.close-btn:hover {  background: var(--btn-hover);  color: var(--text);}
.settings {
  flex: 1;
  padding: 6px 10px;
  overflow-y: auto;
}

.section-title {
  font-size: 11px;
  color: var(--dim);
  margin: 8px 4px 4px;
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 32px;
  background: var(--card);
  border-radius: 8px;
  padding: 0 14px;
  margin-bottom: 4px;
  cursor: pointer;
}

.row-label { font-size: 12px; }
.row-value { font-size: 12px; color: var(--accent); font-family: var(--mono); }

/* Inline Editor */
.inline-editor {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--card2);
  border-radius: 8px;
  padding: 8px 14px;
  margin-bottom: 8px;
  animation: slide-down 0.2s ease;
}

@keyframes slide-down {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.slider {
  flex: 1;
  height: 4px;
  border-radius: 2px;
  background: var(--bar-bg);
  outline: none;
  -webkit-appearance: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
}

.slider::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
  border: none;
}

.slider-value {
  font-size: 11px;
  font-family: var(--mono);
  color: var(--accent);
  min-width: 50px;
  text-align: right;
}

.text-input {
  flex: 1;
  padding: 4px 8px;
  font-size: 11px;
  background: var(--card);
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
  color: var(--text);
  font-family: var(--mono);
  outline: none;
}

.text-input:focus {
  border-color: var(--accent);
}

.grid-editor {
  flex-wrap: wrap;
}

.grid-input {
  display: flex;
  align-items: center;
  gap: 6px;
}

.grid-input label {
  font-size: 11px;
  color: var(--dim);
}

.grid-input input {
  width: 50px;
  padding: 4px 8px;
  font-size: 11px;
  background: var(--card);
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
  color: var(--text);
  font-family: var(--mono);
  text-align: center;
}

.btn-save,
.btn-cancel {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.btn-save {
  background: var(--accent);
  color: var(--bg);
}

.btn-save:hover {
  opacity: 0.9;
}

.btn-cancel {
  background: var(--card);
  color: var(--dim);
}

.btn-cancel:hover {
  background: var(--btn-hover);
  color: var(--text);
}

/* Toggle */
.toggle {
  width: 26px; height: 14px;
  border-radius: 7px;
  background: var(--dim);
  position: relative;
  transition: background 0.2s;
}
.toggle.on { background: var(--accent); }
.toggle-knob {
  width: 10px; height: 10px;
  border-radius: 50%;
  background: var(--card);
  position: absolute;
  top: 2px; left: 2px;
  transition: left 0.2s;
}
.toggle.on .toggle-knob { left: 14px; background: #fff; }

/* Radio */
.radio-row {
  display: flex;
  align-items: center;
  height: 28px;
  background: var(--card);
  border-radius: 8px;
  padding: 0 14px;
  margin-bottom: 4px;
  gap: 8px;
  cursor: pointer;
}
.radio-row.active { background: var(--accent-glow); }

.radio-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  border: 1px solid var(--dim);
}
.radio-dot.checked { background: var(--accent); border-color: var(--accent); }

.radio-label { font-size: 12px; }
.radio-row.active .radio-label { color: var(--accent); }

/* Stats */
.stat-row {
  display: flex;
  align-items: center;
  height: 28px;
  background: var(--card);
  border-radius: 8px;
  padding: 0 14px;
  margin-bottom: 3px;
}
.stat-label { flex: 1; font-size: 11px; }
.stat-ago { font-size: 10px; color: var(--dim); margin-right: 8px; }
.stat-count { font-size: 11px; color: var(--accent); font-family: var(--mono); }
</style>

const closeWindow = () => {
  if (window.electronAPI?.closeWindow) {
    window.electronAPI.closeWindow()
  } else {
    window.close()
  }
}
</script>
