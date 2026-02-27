<template>
  <div v-if="show" class="modal-mask" @click="close">
    <div class="modal-box" @click.stop>
      <div class="modal-header">
        <span class="modal-title">保存到页面</span>
        <button class="close-btn" @click="close">×</button>
      </div>

      <div class="modal-body">
        <div class="form-group">
          <label>选择页面</label>
          <select v-model="selectedPage">
            <option v-for="(page, idx) in pages" :key="idx" :value="idx">
              {{ page.name || `页面 ${idx + 1}` }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>选择位置</label>
          <div class="position-grid">
            <div
              v-for="i in 28"
              :key="i"
              :class="['pos-cell', { selected: selectedPosition === i - 1, filled: isPositionFilled(i - 1) }]"
              @click="selectedPosition = i - 1"
            >
              {{ i }}
            </div>
          </div>
        </div>

        <div class="form-group">
          <label>动作名称</label>
          <input v-model="actionLabel" placeholder="流程名称" />
        </div>

        <div class="form-group">
          <label>图标</label>
          <input v-model="actionIcon" placeholder="emoji" maxlength="2" />
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-cancel" @click="close">取消</button>
        <button class="btn-save" @click="save" :disabled="!canSave">保存</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Page } from '@/types/action'

const props = defineProps<{
  show: boolean
  pages: Page[]
}>()

const emit = defineEmits<{
  close: []
  save: [pageIdx: number, actionIdx: number, label: string, icon: string]
}>()

const selectedPage = ref(0)
const selectedPosition = ref(0)
const actionLabel = ref('')
const actionIcon = ref('🔀')

watch(() => props.show, (show) => {
  if (show) {
    selectedPage.value = 0
    selectedPosition.value = 0
    actionLabel.value = '新流程'
    actionIcon.value = '🔀'
  }
})

const currentPage = computed(() => props.pages[selectedPage.value])

const isPositionFilled = (pos: number) => {
  if (!currentPage.value) return false
  return currentPage.value.actions.some(a => a.index === pos)
}

const canSave = computed(() => {
  return actionLabel.value.trim() !== '' && actionIcon.value.trim() !== ''
})

const close = () => emit('close')

const save = () => {
  if (canSave.value) {
    emit('save', selectedPage.value, selectedPosition.value, actionLabel.value, actionIcon.value)
  }
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
  max-width: 420px;
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

.position-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 4px;
}

.pos-cell {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--card);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  font-size: 11px;
  font-family: var(--mono);
  color: var(--dim);
  cursor: pointer;
  transition: all 0.15s;
}

.pos-cell:hover {
  border-color: var(--accent);
  background: var(--btn-hover);
}

.pos-cell.selected {
  background: var(--accent-glow);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
}

.pos-cell.filled {
  background: var(--red-glow);
  border-color: var(--red);
  color: var(--red);
}

.pos-cell.filled.selected {
  background: var(--yellow-glow);
  border-color: var(--yellow);
  color: var(--yellow);
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

.btn-save:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-save:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
