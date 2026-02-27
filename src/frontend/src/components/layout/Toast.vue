<template>
  <teleport to="body">
    <div class="toast-wrap">
      <transition-group name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="['toast', toast.type]"
          @click="remove(toast.id)"
        >
          {{ toast.message }}
        </div>
      </transition-group>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { useToast } from '@/composables/useToast'
const { toasts, remove } = useToast()
</script>

<style scoped>
.toast-wrap {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  pointer-events: none;
}

.toast {
  padding: 4px 16px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  pointer-events: auto;
  cursor: pointer;
  font-family: var(--mono);
}

.toast.success { background: var(--green-glow); color: var(--green); }
.toast.error { background: var(--red-glow); color: var(--red); }
.toast.warning { background: var(--yellow-glow); color: var(--yellow); }
.toast.info { background: var(--accent-glow); color: var(--accent); }

.toast-enter-active { transition: all 0.3s ease; }
.toast-leave-active { transition: all 0.2s ease; }
.toast-enter-from { opacity: 0; transform: translateY(10px); }
.toast-leave-to { opacity: 0; transform: translateY(-10px); }
</style>
