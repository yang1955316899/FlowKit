<template>
  <div class="coordinate-picker">
    <button
      @click="pickCoordinate"
      :disabled="picking"
      class="pick-btn"
      :class="{ picking }"
    >
      <span class="icon">🎯</span>
      {{ picking ? '点击屏幕选择坐标...' : '拾取坐标' }}
    </button>

    <div v-if="coordinate" class="coordinate-display">
      <span class="label">坐标:</span>
      <span class="value">{{ coordinate.x }}, {{ coordinate.y }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/api'

interface Coordinate {
  x: number
  y: number
}

const emit = defineEmits<{
  picked: [coordinate: Coordinate]
}>()

const picking = ref(false)
const coordinate = ref<Coordinate | null>(null)

const pickCoordinate = async () => {
  picking.value = true
  try {
    const result = await api.post<Coordinate>('/input/pick-coordinate', {
      timeout: 30
    })
    coordinate.value = result
    emit('picked', result)
  } catch (error) {
    console.error('Failed to pick coordinate:', error)
  } finally {
    picking.value = false
  }
}
</script>

<style scoped>
.coordinate-picker {
  display: flex;
  align-items: center;
  gap: 12px;
}

.pick-btn {
  padding: 8px 16px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-card);
  color: var(--color-text);
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.pick-btn:hover:not(:disabled) {
  background: var(--color-bg-secondary);
  border-color: var(--color-accent);
}

.pick-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.pick-btn.picking {
  background: var(--color-accent);
  color: white;
  border-color: var(--color-accent);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

.icon {
  font-size: 16px;
}

.coordinate-display {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--color-bg-secondary);
  border-radius: 6px;
  font-size: 13px;
}

.label {
  color: var(--color-text-secondary);
}

.value {
  font-family: monospace;
  font-weight: 500;
  color: var(--color-accent);
}
</style>
