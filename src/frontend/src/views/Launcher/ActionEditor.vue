<template>
  <div v-if="show" class="modal-mask" @click="close">
    <div
      class="modal-box"
      role="dialog"
      aria-modal="true"
      :aria-label="isEdit ? '编辑动作' : '新建动作'"
      @click.stop
    >
      <div class="modal-header">
        <span class="modal-title">{{ isEdit ? '编辑动作' : '新建动作' }}</span>
        <button class="close-btn" aria-label="关闭" @click="close">×</button>
      </div>

      <div class="modal-body">
        <!-- 类型选择 -->
        <div class="form-group">
          <label for="action-type">类型</label>
          <select id="action-type" v-model="form.type" :disabled="isEdit" aria-required="true">
            <option value="app">应用</option>
            <option value="url">网址</option>
            <option value="combo">组合</option>
            <option value="shell">命令</option>
            <option value="snippet">文本</option>
            <option value="keys">按键</option>
            <option value="script">脚本</option>
          </select>
        </div>

        <!-- 标签 -->
        <div class="form-group">
          <label for="action-label">标签</label>
          <input id="action-label" v-model="form.label" placeholder="动作名称" aria-required="true" />
        </div>

        <!-- 图标 -->
        <div class="form-group">
          <label for="action-icon">图标</label>
          <input id="action-icon" v-model="form.icon" placeholder="emoji 图标" maxlength="2" />
        </div>

        <!-- 快捷键 -->
        <div class="form-group">
          <label for="action-hotkey">快捷键</label>
          <input
            id="action-hotkey"
            v-model="form.hotkey"
            placeholder="例如: ctrl+shift+a"
            aria-describedby="hotkey-hint"
            @keydown="recordHotkey"
          />
          <span id="hotkey-hint" class="sr-only">按下键盘组合键自动记录</span>
        </div>

        <!-- 目标 (app/url/shell/snippet/keys/script) -->
        <div v-if="needsTarget" class="form-group">
          <label for="action-target">{{ targetLabel }}</label>
          <input id="action-target" v-model="form.target" :placeholder="targetPlaceholder" aria-required="true" />
        </div>

        <!-- Combo 步骤 -->
        <div v-if="form.type === 'combo'" class="form-group">
          <label>步骤</label>
          <div class="steps-list" role="list">
            <div v-for="(step, idx) in form.steps" :key="idx" class="step-item" role="listitem">
              <span class="step-num">{{ idx + 1 }}</span>
              <span class="step-type">{{ step.type }}</span>
              <button class="step-del" :aria-label="`删除步骤 ${idx + 1}`" @click="removeStep(idx)">×</button>
            </div>
            <button class="add-step-btn" @click="addStep">+ 添加步骤</button>
          </div>
        </div>

        <!-- Combo 延迟 -->
        <div v-if="form.type === 'combo'" class="form-group">
          <label for="action-delay">延迟 (ms)</label>
          <input id="action-delay" v-model.number="form.delay" type="number" min="0" />
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-cancel" @click="close">取消</button>
        <button class="btn-save" @click="save">保存</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Action, FlowStep } from '@/types/action'
import type {
  AppAction, UrlAction, ShellAction, SnippetAction,
  KeysAction, ScriptAction, ComboAction
} from '@/types/action'
import { FLOW_STEP_DEFAULTS } from '@/constants'

const props = defineProps<{
  show: boolean
  action?: Action | null
}>()

const emit = defineEmits<{
  close: []
  save: [action: Partial<Action>]
}>()

const isEdit = computed(() => !!props.action)

const form = ref({
  type: 'app' as Action['type'],
  label: '',
  icon: '',
  hotkey: '',
  target: '',
  steps: [] as FlowStep[],
  delay: FLOW_STEP_DEFAULTS.DELAY_DURATION
})

watch(() => props.show, (show) => {
  if (show && props.action) {
    const action = props.action
    form.value = {
      type: action.type,
      label: action.label,
      icon: action.icon,
      hotkey: action.hotkey || '',
      target: 'target' in action ? action.target : '',
      steps: action.type === 'combo' ? action.steps : [],
      delay: action.type === 'combo' ? action.delay : FLOW_STEP_DEFAULTS.DELAY_DURATION
    }
  } else if (show) {
    form.value = {
      type: 'app',
      label: '',
      icon: '✦',
      hotkey: '',
      target: '',
      steps: [],
      delay: FLOW_STEP_DEFAULTS.DELAY_DURATION
    }
  }
})

const needsTarget = computed(() => {
  return ['app', 'url', 'shell', 'snippet', 'keys', 'script'].includes(form.value.type)
})

const targetLabel = computed(() => {
  const labels: Record<string, string> = {
    app: '应用路径',
    url: '网址',
    shell: '命令',
    snippet: '文本内容',
    keys: '按键序列',
    script: '脚本代码'
  }
  return labels[form.value.type] || '目标'
})

const targetPlaceholder = computed(() => {
  const placeholders: Record<string, string> = {
    app: 'C:\\Program Files\\App\\app.exe',
    url: 'https://example.com',
    shell: 'echo Hello',
    snippet: '要复制的文本',
    keys: 'ctrl+c',
    script: 'print("Hello")'
  }
  return placeholders[form.value.type] || ''
})

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
    form.value.hotkey = keys.join('+')
  }
}

const addStep = () => {
  form.value.steps.push({ type: 'delay', duration: FLOW_STEP_DEFAULTS.DELAY_DURATION })
}

const removeStep = (idx: number) => {
  form.value.steps.splice(idx, 1)
}

const close = () => emit('close')

const save = () => {
  const baseData = {
    type: form.value.type,
    label: form.value.label,
    icon: form.value.icon,
    hotkey: form.value.hotkey || undefined
  }

  let data: Partial<Action>

  if (form.value.type === 'combo') {
    data = {
      ...baseData,
      type: 'combo',
      steps: form.value.steps,
      delay: form.value.delay
    } as Partial<ComboAction>
  } else if (needsTarget.value) {
    data = {
      ...baseData,
      target: form.value.target
    } as Partial<AppAction | UrlAction | ShellAction | SnippetAction | KeysAction | ScriptAction>
  } else {
    data = baseData
  }

  emit('save', data)
}
</script>

<style scoped>
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fade-in 0.2s ease;
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-box {
  background: var(--card2);
  border: 1px solid var(--border);
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  animation: scale-in 0.25s ease;
}

@keyframes scale-in {
  from { transform: scale(0.9); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-subtle);
}

.modal-title {
  font-size: 13px;
  font-weight: 600;
}

.close-btn {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  font-size: 18px;
  color: var(--dim);
  transition: all 0.15s;
}

.close-btn:hover {
  background: var(--btn-hover);
  color: var(--text);
}

.modal-body {
  flex: 1;
  padding: 12px 16px;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  font-size: 11px;
  color: var(--dim);
  margin-bottom: 4px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 6px 10px;
  font-size: 12px;
  background: var(--card);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  color: var(--text);
  outline: none;
  transition: border-color 0.15s;
}

.form-group input:focus,
.form-group select:focus {
  border-color: var(--accent);
}

.steps-list {
  background: var(--card);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  padding: 6px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  background: var(--card2);
  border-radius: 4px;
  margin-bottom: 4px;
  font-size: 11px;
}

.step-num {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-glow);
  color: var(--accent);
  border-radius: 50%;
  font-size: 9px;
  font-family: var(--mono);
}

.step-type {
  flex: 1;
  color: var(--sub);
}

.step-del {
  width: 18px;
  height: 18px;
  border-radius: 4px;
  font-size: 14px;
  color: var(--dim);
  transition: all 0.15s;
}

.step-del:hover {
  background: var(--red-glow);
  color: var(--red);
}

.add-step-btn {
  width: 100%;
  padding: 4px;
  font-size: 11px;
  color: var(--accent);
  background: var(--accent-glow);
  border-radius: 4px;
  transition: background 0.15s;
}

.add-step-btn:hover {
  background: var(--btn-hover);
}

.modal-footer {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid var(--border-subtle);
}

.btn-cancel,
.btn-save {
  flex: 1;
  padding: 6px;
  font-size: 12px;
  border-radius: 6px;
  transition: all 0.15s;
}

.btn-cancel {
  background: var(--card);
  color: var(--sub);
}

.btn-cancel:hover {
  background: var(--btn-hover);
  color: var(--text);
}

.btn-save {
  background: var(--accent);
  color: var(--bg);
  font-weight: 600;
}

.btn-save:hover {
  opacity: 0.9;
}
</style>
