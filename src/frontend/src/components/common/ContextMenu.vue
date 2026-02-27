<template>
  <teleport to="body">
    <div
      v-if="show"
      class="context-menu"
      role="menu"
      aria-label="上下文菜单"
      :style="{ left: x + 'px', top: y + 'px' }"
      @click="close"
    >
      <div
        v-for="(item, idx) in items"
        :key="idx"
        :class="['menu-item', { disabled: item.disabled, danger: item.danger }]"
        role="menuitem"
        :aria-disabled="item.disabled"
        :tabindex="item.disabled ? -1 : 0"
        @click="!item.disabled && handleClick(item)"
        @keydown.enter="!item.disabled && handleClick(item)"
        @keydown.space.prevent="!item.disabled && handleClick(item)"
      >
        <span v-if="item.icon" class="item-icon" aria-hidden="true">{{ item.icon }}</span>
        <span class="item-label">{{ item.label }}</span>
        <span v-if="item.shortcut" class="item-shortcut" aria-label="快捷键">{{ item.shortcut }}</span>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'

export interface MenuItem {
  label: string
  icon?: string
  shortcut?: string
  disabled?: boolean
  danger?: boolean
  action: () => void
}

const props = defineProps<{
  show: boolean
  x: number
  y: number
  items: MenuItem[]
}>()

const emit = defineEmits<{
  close: []
}>()

const close = () => emit('close')

const handleClick = (item: MenuItem) => {
  item.action()
  close()
}

const handleClickOutside = (e: MouseEvent) => {
  if (props.show) {
    close()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.context-menu {
  position: fixed;
  background: var(--card2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 4px;
  min-width: 160px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
  z-index: 2000;
  animation: menu-appear 0.15s ease;
}

@keyframes menu-appear {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.15s;
  user-select: none;
}

.menu-item:hover:not(.disabled) {
  background: var(--btn-hover);
}

.menu-item.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.menu-item.danger {
  color: var(--red);
}

.menu-item.danger:hover:not(.disabled) {
  background: var(--red-glow);
}

.item-icon {
  font-size: 14px;
}

.item-label {
  flex: 1;
}

.item-shortcut {
  font-size: 10px;
  color: var(--dim);
  font-family: var(--mono);
}
</style>
