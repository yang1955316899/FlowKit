<template>
  <div class="launcher" @wheel="onWheel">
    <!-- 搜索栏 -->
    <div class="search-bar" @click="focusSearch">
      <span class="search-icon">🔍</span>
      <input
        ref="searchInput"
        v-model="searchQuery"
        placeholder="搜索动作..."
        class="search-field"
        @input="handleSearch"
        @keydown.escape="clearSearch"
        @keydown.up.prevent="navigateResults(-1)"
        @keydown.down.prevent="navigateResults(1)"
        @keydown.enter.prevent="selectCurrentResult"
        @focus="showSearchResults = true"
        @blur="onSearchBlur"
      />
      <button class="new-flow-btn" @click="openFlowEditorWindow" title="新建流程">🔀</button>

      <!-- Search Results Dropdown -->
      <SearchResults
        :show="showSearchResults && (searchResults.length > 0 || searchHistory.length > 0 || searchQuery.trim().length > 0)"
        :query="searchQuery"
        :results="searchResults"
        :history="searchHistory"
        :selected-index="selectedResultIndex"
        @select="onSelectResult"
        @select-history="onSelectHistory"
        @clear-history="clearSearchHistory"
      />
    </div>

    <!-- 页面名 -->
    <div class="page-name">{{ pageName || '工具' }}</div>

    <!-- 动作网格 -->
    <div class="action-grid" :style="gridStyle">
      <div
        v-for="(action, idx) in displayActions"
        :key="idx"
        :class="[
          'cell',
          {
            filled: !!action,
            empty: !action,
            dragging: dragState.draggedIndex === idx,
            'drop-target': dragState.dropTargetIndex === idx && dragState.canDrop
          }
        ]"
        :draggable="!!action"
        @click="action && executeAction(action.index!)"
        @contextmenu.prevent="action && onRightClick($event, idx, action)"
        @dragstart="onDragStart($event, idx)"
        @dragover.prevent="onDragOver($event, idx)"
        @dragleave="onDragLeave"
        @drop="onDrop($event, idx)"
        @dragend="onDragEnd"
      >
        <template v-if="action">
          <span class="cell-icon">{{ action.icon || '✦' }}</span>
          <span class="cell-label">{{ truncLabel(action.label) }}</span>
          <span v-if="action.type === 'combo'" class="group-badge">
            {{ action.steps?.length || 0 }}
          </span>
        </template>
      </div>
    </div>

    <!-- 页码圆点 -->
    <div v-if="totalPages > 1" class="page-dots">
      <span
        v-for="i in totalPages"
        :key="i"
        :class="['dot', { active: currentPage === i - 1 }]"
        @click="changePage(i - 1)"
      />
    </div>

    <!-- 右键菜单 -->
    <ContextMenu
      :show="contextMenu.show"
      :x="contextMenu.x"
      :y="contextMenu.y"
      :items="contextMenu.items"
      @close="contextMenu.show = false"
    />

    <!-- 动作编辑器 -->
    <ActionEditor
      :show="editor.show"
      :action="editor.action"
      @close="editor.show = false"
      @save="handleSave"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useLauncherStore } from '@/stores/launcher'
import { useAppStore } from '@/stores/app'
import { useToast } from '@/composables/useToast'
import { useSearchHistory } from '@/composables/useSearchHistory'
import { useDragAndDrop } from '@/composables/useDragAndDrop'
import { useKeyboard } from '@/composables/useKeyboard'
import { isElectron, openFlowEditor } from '@/electron'
import { truncateText } from '@/utils'
import { GRID_CONFIG, KEYBOARD_SHORTCUTS } from '@/constants'
import type { Action, SearchResult as SearchResultType, ComboAction } from '@/types/action'
import ContextMenu, { type MenuItem } from '@/components/common/ContextMenu.vue'
import ActionEditor from './ActionEditor.vue'
import SearchResults from '@/components/launcher/SearchResults.vue'

const store = useLauncherStore()
const appStore = useAppStore()
const { success, error } = useToast()
const { history: searchHistory, addToHistory, clearHistory: clearSearchHistory } = useSearchHistory()
const dragState = useDragAndDrop()

const searchInput = ref<HTMLInputElement>()
const searchQuery = ref('')
const showSearchResults = ref(false)
const selectedResultIndex = ref(-1)
const dragIndex = ref<number | null>(null)

const cols = GRID_CONFIG.COLS
const rows = GRID_CONFIG.ROWS

const currentPage = computed(() => store.currentPage)
const pageName = computed(() => store.pageName)
const totalPages = computed(() => store.totalPages)
const actions = computed(() => store.actions)
const searchResults = computed(() => store.searchResults)

const gridStyle = computed(() => ({
  gridTemplateColumns: `repeat(${cols}, 1fr)`,
  gridTemplateRows: `repeat(${rows}, 52px)`,
}))

const displayActions = computed(() => {
  const total = cols * rows
  const result = [...actions.value]
  while (result.length < total) result.push(null as any)
  return result.slice(0, total)
})

const truncLabel = (label?: string) => {
  return truncateText(label || '', 8)
}

const focusSearch = () => searchInput.value?.focus()

const handleSearch = () => {
  selectedResultIndex.value = -1
  if (searchQuery.value.trim()) {
    store.search(searchQuery.value)
    showSearchResults.value = true
  } else {
    store.clearSearch()
  }
}

const clearSearch = () => {
  searchQuery.value = ''
  store.clearSearch()
  showSearchResults.value = false
  selectedResultIndex.value = -1
}

const onSearchBlur = () => {
  // Delay hiding to allow click events on results
  setTimeout(() => {
    showSearchResults.value = false
  }, 200)
}

const navigateResults = (direction: number) => {
  const totalItems = searchHistory.value.length + searchResults.value.length
  if (totalItems === 0) return

  selectedResultIndex.value = Math.max(
    -1,
    Math.min(totalItems - 1, selectedResultIndex.value + direction)
  )
}

const selectCurrentResult = () => {
  const historyLength = searchHistory.value.length

  if (selectedResultIndex.value < 0) {
    // No selection, just search
    if (searchQuery.value.trim()) {
      addToHistory(searchQuery.value)
    }
    return
  }

  if (selectedResultIndex.value < historyLength) {
    // Select from history
    const historyItem = searchHistory.value[selectedResultIndex.value]
    onSelectHistory(historyItem)
  } else {
    // Select from results
    const resultIndex = selectedResultIndex.value - historyLength
    const result = searchResults.value[resultIndex]
    if (result) {
      onSelectResult(result)
    }
  }
}

const onSelectResult = async (result: SearchResultType) => {
  addToHistory(searchQuery.value)
  showSearchResults.value = false

  // Navigate to the page and execute the action
  if (result.page !== currentPage.value) {
    await changePage(result.page)
  }

  try {
    await store.executeAction(result.index)
    success('已执行')
  } catch {
    error('执行失败')
  }

  clearSearch()
}

const onSelectHistory = (query: string) => {
  searchQuery.value = query
  handleSearch()
  searchInput.value?.focus()
}

const executeAction = async (idx: number) => {
  try {
    await store.executeAction(idx)
  } catch {
    error('执行失败')
  }
}

const changePage = (page: number) => store.fetchActions(page)

const onWheel = (e: WheelEvent) => {
  if (totalPages.value <= 1) return
  if (e.deltaY < 0) changePage(Math.max(0, currentPage.value - 1))
  else changePage(Math.min(totalPages.value - 1, currentPage.value + 1))
}

// Context Menu
const contextMenu = reactive({
  show: false,
  x: 0,
  y: 0,
  items: [] as MenuItem[],
  targetIndex: -1,
  targetAction: null as Action | null
})

const onRightClick = (e: MouseEvent, idx: number, action: Action) => {
  contextMenu.targetIndex = idx
  contextMenu.targetAction = action
  contextMenu.x = e.clientX
  contextMenu.y = e.clientY
  contextMenu.items = [
    {
      label: '执行',
      icon: '▶',
      action: () => executeAction(action.index!)
    },
    {
      label: '编辑',
      icon: '✏',
      action: () => openEditor(action)
    },
    {
      label: '复制',
      icon: '📋',
      action: () => copyAction(action)
    },
    {
      label: '导出',
      icon: '📤',
      action: () => exportAction(action)
    },
    {
      label: '删除',
      icon: '🗑',
      danger: true,
      action: () => deleteAction(action.index!)
    }
  ]
  contextMenu.show = true
}

// Action Editor
const editor = reactive({
  show: false,
  action: null as Action | null
})

const openEditor = (action?: Action) => {
  editor.action = action || null
  editor.show = true
}

const handleSave = async (data: Partial<Action>) => {
  try {
    if (editor.action) {
      await store.updateAction(editor.action.index!, data)
      success('已更新')
    } else {
      await store.addAction(data)
      success('已添加')
    }
    editor.show = false
  } catch {
    error('保存失败')
  }
}

const copyAction = async (action: Action) => {
  try {
    const copy = { ...action }
    delete copy.index
    delete copy.id
    copy.label = copy.label + ' (副本)'
    await store.addAction(copy)
    success('已复制')
  } catch {
    error('复制失败')
  }
}

const exportAction = (action: Action) => {
  const json = JSON.stringify(action, null, 2)
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${action.label}.json`
  a.click()
  URL.revokeObjectURL(url)
  success('已导出')
}

const deleteAction = async (idx: number) => {
  try {
    await store.deleteAction(idx)
    success('已删除')
  } catch {
    error('删除失败')
  }
}

// Drag and Drop
const onDragStart = (e: DragEvent, idx: number) => {
  dragIndex.value = idx
  dragState.startDrag(idx)
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', idx.toString())
  }
}

const onDragOver = (e: DragEvent, idx: number) => {
  if (dragIndex.value !== null && dragIndex.value !== idx) {
    e.preventDefault()
    dragState.setDropTarget(idx)
    if (e.dataTransfer) {
      e.dataTransfer.dropEffect = 'move'
    }
  }
}

const onDragLeave = () => {
  dragState.setDropTarget(null)
}

const onDrop = async (e: DragEvent, toIdx: number) => {
  e.preventDefault()
  if (dragIndex.value !== null && dragIndex.value !== toIdx) {
    const fromAction = displayActions.value[dragIndex.value]
    const toAction = displayActions.value[toIdx]

    if (fromAction && fromAction.index !== undefined) {
      const fromGlobalIdx = fromAction.index
      const toGlobalIdx = toAction?.index ?? toIdx

      try {
        await store.reorderActions(fromGlobalIdx, toGlobalIdx)
        success('已移动')
      } catch {
        error('移动失败')
      }
    }
  }
  dragIndex.value = null
  dragState.endDrag()
}

const onDragEnd = () => {
  dragIndex.value = null
  dragState.endDrag()
}

// Keyboard shortcuts
useKeyboard([
  {
    key: 'k',
    ctrl: true,
    handler: () => focusSearch(),
    description: '聚焦搜索框'
  },
  {
    key: 'n',
    ctrl: true,
    handler: () => openEditor(null),
    description: '新建动作'
  }
])

const openFlowEditorWindow = () => {
  if (isElectron()) {
    // Electron: 打开新窗口
    openFlowEditor()
  } else {
    // 浏览器: 显示 Dialog
    appStore.setShowFlowEditor(true)
  }
}

onMounted(() => store.fetchActions())
</script>

<style scoped>
.launcher {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 6px 10px;
  overflow: hidden;
}

.search-bar {
  position: relative;
  display: flex;
  align-items: center;
  height: 24px;
  background: var(--card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 0 10px;
  gap: 6px;
  cursor: text;
}

.search-icon { font-size: 10px; }

.search-field {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--dim);
  font-size: 11px;
  padding: 0;
  outline: none;
}

.new-flow-btn {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 6px;
  background: var(--accent-glow);
  color: var(--accent);
  transition: all 0.15s;
  cursor: pointer;
}

.new-flow-btn:hover {
  background: var(--accent);
  color: var(--bg);
}

.page-name {
  font-size: 11px;
  color: var(--dim);
  margin: 6px 4px 4px;
}

.action-grid {
  flex: 1;
  display: grid;
  gap: 6px;
}

.cell {
  background: var(--btn-bg);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
  transition: all 0.15s;
}

.cell.filled:hover {
  background: var(--btn-hover);
  border-color: var(--accent);
}

.cell.filled:active {
  background: var(--btn-active);
}

.cell.dragging {
  opacity: 0.5;
  transform: scale(0.95);
}

.cell.drop-target {
  background: var(--accent-glow);
  border: 2px dashed var(--accent);
  transform: scale(1.05);
}

.cell.empty {
  background: var(--card);
  border: 1px solid var(--border-subtle);
  cursor: default;
}

.cell-icon {
  font-size: 20px;
  line-height: 1;
}

.cell-label {
  font-size: 10px;
  color: var(--dim);
  margin-top: 2px;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: center;
  padding: 0 2px;
}

.group-badge {
  position: absolute;
  top: 3px;
  right: 5px;
  font-size: 9px;
  color: var(--accent);
  font-family: var(--mono);
}

.page-dots {
  display: flex;
  justify-content: center;
  gap: 10px;
  padding: 8px 0 4px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--dim);
  cursor: pointer;
  transition: all 0.2s;
}

.dot.active {
  background: var(--accent);
}
</style>
