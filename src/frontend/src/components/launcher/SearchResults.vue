<template>
  <div v-if="show" class="search-results">
    <!-- Search history -->
    <div v-if="showHistory && history.length > 0" class="results-section">
      <div class="section-header">
        <span class="section-title">最近搜索</span>
        <button class="clear-btn" @click="$emit('clear-history')">清除</button>
      </div>
      <div
        v-for="(item, idx) in history"
        :key="`history-${idx}`"
        class="result-item"
        :class="{ active: idx === selectedIndex }"
        @click="$emit('select-history', item)"
        @mouseenter="selectedIndex = idx"
      >
        <span class="result-icon">🕒</span>
        <span class="result-text">{{ item }}</span>
      </div>
    </div>

    <!-- Search results -->
    <div v-if="results.length > 0" class="results-section">
      <div class="section-header">
        <span class="section-title">搜索结果 ({{ results.length }})</span>
      </div>
      <div
        v-for="(result, idx) in results"
        :key="result.id"
        class="result-item"
        :class="{ active: idx + historyOffset === selectedIndex }"
        @click="$emit('select', result)"
        @mouseenter="selectedIndex = idx + historyOffset"
      >
        <span class="result-icon">{{ result.icon }}</span>
        <div class="result-content">
          <div class="result-label">
            <span v-html="highlightMatch(result.label, query)"></span>
            <span class="result-type">{{ getTypeLabel(result.type) }}</span>
          </div>
          <div class="result-meta">
            <span class="result-page">{{ result.pageName }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- No results -->
    <div v-if="!showHistory && results.length === 0 && query" class="no-results">
      <span class="no-results-icon">🔍</span>
      <span class="no-results-text">未找到匹配结果</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { SearchResult } from '@/types/action'

const props = defineProps<{
  show: boolean
  query: string
  results: SearchResult[]
  history: string[]
  selectedIndex?: number
}>()

const emit = defineEmits<{
  select: [result: SearchResult]
  'select-history': [query: string]
  'clear-history': []
}>()

const selectedIndex = ref(props.selectedIndex ?? -1)

// Show history when query is empty
const showHistory = computed(() => !props.query.trim() && props.history.length > 0)

// Offset for keyboard navigation (history items come first)
const historyOffset = computed(() => showHistory.value ? props.history.length : 0)

// Watch for external selectedIndex changes
watch(() => props.selectedIndex, (newIndex) => {
  if (newIndex !== undefined) {
    selectedIndex.value = newIndex
  }
})

// Highlight matching text in search results
const highlightMatch = (text: string, query: string): string => {
  if (!query.trim()) return text

  const regex = new RegExp(`(${escapeRegex(query)})`, 'gi')
  return text.replace(regex, '<mark>$1</mark>')
}

// Escape special regex characters
const escapeRegex = (str: string): string => {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// Get type label in Chinese
const getTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    app: '应用',
    url: '网址',
    combo: '组合',
    shell: '命令',
    snippet: '文本',
    keys: '按键',
    script: '脚本'
  }
  return labels[type] || type
}
</script>

<style scoped>
.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 8px;
  background: var(--card2);
  border: 1px solid var(--border);
  border-radius: 8px;
  max-height: 400px;
  overflow-y: auto;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  animation: slide-down 0.2s ease;
}

@keyframes slide-down {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.results-section {
  padding: 8px 0;
}

.results-section + .results-section {
  border-top: 1px solid var(--border-subtle);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  margin-bottom: 4px;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.clear-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 12px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.15s ease;
}

.clear-btn:hover {
  background: var(--hover);
  color: var(--text);
}

.result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.result-item:hover,
.result-item.active {
  background: var(--hover);
}

.result-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.result-text {
  flex: 1;
  color: var(--text);
  font-size: 14px;
}

.result-content {
  flex: 1;
  min-width: 0;
}

.result-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text);
  margin-bottom: 4px;
}

.result-label :deep(mark) {
  background: var(--accent);
  color: var(--bg);
  padding: 2px 4px;
  border-radius: 3px;
  font-weight: 600;
}

.result-type {
  font-size: 11px;
  color: var(--text-muted);
  background: var(--card);
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted);
}

.result-page {
  display: flex;
  align-items: center;
  gap: 4px;
}

.result-page::before {
  content: '📄';
  font-size: 10px;
}

.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  gap: 12px;
}

.no-results-icon {
  font-size: 32px;
  opacity: 0.5;
}

.no-results-text {
  font-size: 14px;
  color: var(--text-muted);
}

/* Scrollbar styling */
.search-results::-webkit-scrollbar {
  width: 8px;
}

.search-results::-webkit-scrollbar-track {
  background: transparent;
}

.search-results::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 4px;
}

.search-results::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}
</style>
