<template>
  <div v-if="visible" class="selection-popup" :style="popupStyle">
    <button @click="copyText" class="action-btn" title="复制">
      <span class="icon">📋</span>
    </button>
    <button @click="searchText" class="action-btn" title="搜索">
      <span class="icon">🔍</span>
    </button>
    <button @click="translateText" class="action-btn" title="翻译">
      <span class="icon">🌐</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'

const visible = ref(false)
const selectedText = ref('')
const position = ref({ x: 0, y: 0 })

const popupStyle = computed(() => ({
  left: `${position.value.x}px`,
  top: `${position.value.y}px`,
}))

const handleSelection = () => {
  const selection = window.getSelection()
  const text = selection?.toString().trim()

  if (text && text.length > 0) {
    selectedText.value = text
    const range = selection?.getRangeAt(0)
    const rect = range?.getBoundingClientRect()

    if (rect) {
      position.value = {
        x: rect.left + rect.width / 2,
        y: rect.top - 40,
      }
      visible.value = true
    }
  } else {
    visible.value = false
  }
}

const copyText = () => {
  navigator.clipboard.writeText(selectedText.value)
  visible.value = false
}

const searchText = () => {
  window.open(`https://www.google.com/search?q=${encodeURIComponent(selectedText.value)}`, '_blank')
  visible.value = false
}

const translateText = () => {
  window.open(`https://translate.google.com/?text=${encodeURIComponent(selectedText.value)}`, '_blank')
  visible.value = false
}

onMounted(() => {
  document.addEventListener('mouseup', handleSelection)
  document.addEventListener('mousedown', () => {
    if (visible.value) {
      visible.value = false
    }
  })
})

onUnmounted(() => {
  document.removeEventListener('mouseup', handleSelection)
})
</script>

<style scoped>
.selection-popup {
  position: fixed;
  display: flex;
  gap: 4px;
  padding: 6px;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 9999;
  transform: translateX(-50%);
}

.action-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.action-btn:hover {
  background: var(--color-bg-secondary);
}

.icon {
  font-size: 16px;
}
</style>
