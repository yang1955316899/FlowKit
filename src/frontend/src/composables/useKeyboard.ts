/**
 * Keyboard shortcuts management composable
 * Provides a centralized way to register and handle keyboard shortcuts
 */

import { onMounted, onUnmounted } from 'vue'

export interface KeyboardShortcut {
  key: string
  ctrl?: boolean
  shift?: boolean
  alt?: boolean
  meta?: boolean
  handler: (event: KeyboardEvent) => void
  description?: string
}

export function useKeyboard(shortcuts: KeyboardShortcut[]) {
  const handleKeyDown = (event: KeyboardEvent) => {
    for (const shortcut of shortcuts) {
      const keyMatch = event.key.toLowerCase() === shortcut.key.toLowerCase()
      const ctrlMatch = shortcut.ctrl === undefined || event.ctrlKey === shortcut.ctrl
      const shiftMatch = shortcut.shift === undefined || event.shiftKey === shortcut.shift
      const altMatch = shortcut.alt === undefined || event.altKey === shortcut.alt
      const metaMatch = shortcut.meta === undefined || event.metaKey === shortcut.meta

      if (keyMatch && ctrlMatch && shiftMatch && altMatch && metaMatch) {
        event.preventDefault()
        shortcut.handler(event)
        break
      }
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', handleKeyDown)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeyDown)
  })

  return {
    shortcuts
  }
}
