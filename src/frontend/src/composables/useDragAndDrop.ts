/**
 * Drag and drop state management composable
 * Provides enhanced drag and drop functionality with visual feedback
 */

import { ref, computed } from 'vue'

export function useDragAndDrop() {
  const isDragging = ref(false)
  const draggedIndex = ref<number | null>(null)
  const dropTargetIndex = ref<number | null>(null)

  const startDrag = (index: number) => {
    isDragging.value = true
    draggedIndex.value = index
  }

  const endDrag = () => {
    isDragging.value = false
    draggedIndex.value = null
    dropTargetIndex.value = null
  }

  const setDropTarget = (index: number | null) => {
    dropTargetIndex.value = index
  }

  const canDrop = computed(() => {
    return (
      isDragging.value &&
      draggedIndex.value !== null &&
      dropTargetIndex.value !== null &&
      draggedIndex.value !== dropTargetIndex.value
    )
  })

  return {
    isDragging: computed(() => isDragging.value),
    draggedIndex: computed(() => draggedIndex.value),
    dropTargetIndex: computed(() => dropTargetIndex.value),
    canDrop,
    startDrag,
    endDrag,
    setDropTarget
  }
}
