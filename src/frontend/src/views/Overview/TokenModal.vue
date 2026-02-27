<template>
  <div v-if="show" class="modal-mask" @click="close">
    <div class="modal-box" @click.stop>
      <div class="modal-header">
        <span class="modal-title">{{ isEdit ? '编辑 Token' : '添加 Token' }}</span>
        <button class="close-btn" @click="close">×</button>
      </div>

      <div class="modal-body">
        <div class="form-group">
          <label>名称</label>
          <input v-model="form.name" placeholder="Token 名称" />
        </div>

        <div class="form-group">
          <label>凭证</label>
          <input v-model="form.credential" placeholder="API Key" type="password" />
        </div>

        <div class="form-group">
          <label>每日限额 ($)</label>
          <input v-model.number="form.daily_limit" type="number" min="0" step="0.01" />
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
import type { Token } from '@/types/token'

const props = defineProps<{
  show: boolean
  token?: Token | null
}>()

const emit = defineEmits<{
  close: []
  save: [data: Partial<Token>]
}>()

const isEdit = computed(() => !!props.token)

const form = ref({
  name: '',
  credential: '',
  daily_limit: 0
})

watch(() => props.show, (show) => {
  if (show && props.token) {
    form.value = {
      name: props.token.name,
      credential: props.token.credential,
      daily_limit: props.token.daily_limit
    }
  } else if (show) {
    form.value = {
      name: '',
      credential: '',
      daily_limit: 0
    }
  }
})

const close = () => emit('close')

const save = () => {
  emit('save', {
    name: form.value.name,
    credential: form.value.credential,
    daily_limit: form.value.daily_limit
  })
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
  max-width: 360px;
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
  padding: 12px 16px;
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

.form-group input {
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

.form-group input:focus {
  border-color: var(--accent);
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
