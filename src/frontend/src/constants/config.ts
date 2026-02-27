/**
 * Application-wide constants
 * Eliminates magic numbers and centralizes configuration
 */

// Grid configuration for Launcher
export const GRID_CONFIG = {
  COLS: 4,
  ROWS: 7,
  TOTAL_SLOTS: 28, // 4 * 7
  GAP: 16, // px
  CARD_MIN_WIDTH: 120, // px
  CARD_MIN_HEIGHT: 100 // px
} as const

// Delay configurations (milliseconds)
export const DELAY_CONFIG = {
  DEBOUNCE_SEARCH: 300,
  DEBOUNCE_INPUT: 500,
  THROTTLE_SCROLL: 100,
  THROTTLE_RESIZE: 200,
  TOAST_DURATION: 3000,
  TOOLTIP_DELAY: 500,
  ANIMATION_DURATION: 200,
  MODAL_TRANSITION: 300
} as const

// API configuration
export const API_CONFIG = {
  TIMEOUT: 10000, // 10 seconds
  RETRY_COUNT: 3,
  RETRY_DELAY: 1000, // 1 second
  BASE_URL: 'http://localhost:8765'
} as const

// Text configuration
export const TEXT_CONFIG = {
  MAX_LABEL_LENGTH: 20,
  MAX_DESCRIPTION_LENGTH: 100,
  MAX_SEARCH_HISTORY: 10,
  TRUNCATE_SUFFIX: '...'
} as const

// Keyboard shortcuts
export const KEYBOARD_SHORTCUTS = {
  SEARCH_FOCUS: 'ctrl+k',
  NEW_ACTION: 'ctrl+n',
  SAVE: 'ctrl+s',
  CLOSE_MODAL: 'escape',
  NAVIGATE_UP: 'arrowup',
  NAVIGATE_DOWN: 'arrowdown',
  NAVIGATE_LEFT: 'arrowleft',
  NAVIGATE_RIGHT: 'arrowright',
  CONFIRM: 'enter'
} as const

// Local storage keys
export const STORAGE_KEYS = {
  SEARCH_HISTORY: 'flowkit_search_history',
  THEME: 'flowkit_theme',
  LAST_PAGE: 'flowkit_last_page',
  USER_PREFERENCES: 'flowkit_preferences'
} as const

// Flow step default values
export const FLOW_STEP_DEFAULTS = {
  DELAY_DURATION: 1000,
  TYPE_TEXT_INTERVAL: 50,
  MOUSE_CLICK_BUTTON: 'left' as const,
  MOUSE_CLICK_COUNT: 1,
  MOUSE_MOVE_DURATION: 500,
  HTTP_TIMEOUT: 5000,
  TOAST_DURATION: 3000,
  TOAST_LEVEL: 'info' as const
} as const

// Validation rules
export const VALIDATION_RULES = {
  MIN_LABEL_LENGTH: 1,
  MAX_LABEL_LENGTH: 50,
  MIN_HOTKEY_LENGTH: 1,
  MAX_HOTKEY_LENGTH: 20,
  MIN_DELAY: 0,
  MAX_DELAY: 60000, // 1 minute
  MIN_STEPS: 1,
  MAX_STEPS: 100
} as const

// HTTP methods
export const HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'] as const

// Toast levels
export const TOAST_LEVELS = ['info', 'success', 'warning', 'error'] as const

// Mouse buttons
export const MOUSE_BUTTONS = ['left', 'right', 'middle'] as const

// Action types
export const ACTION_TYPES = ['app', 'url', 'combo', 'shell', 'snippet', 'keys', 'script'] as const

// Flow step types
export const FLOW_STEP_TYPES = [
  'delay',
  'keys',
  'type_text',
  'app',
  'shell',
  'url',
  'snippet',
  'toast',
  'mouse_click',
  'mouse_move',
  'set_var',
  'http_request',
  'conditional'
] as const

// Z-index layers
export const Z_INDEX = {
  BASE: 0,
  DROPDOWN: 1000,
  STICKY: 1020,
  FIXED: 1030,
  MODAL_BACKDROP: 1040,
  MODAL: 1050,
  POPOVER: 1060,
  TOOLTIP: 1070,
  TOAST: 1080
} as const

// Breakpoints (for responsive design if needed)
export const BREAKPOINTS = {
  XS: 480,
  SM: 640,
  MD: 768,
  LG: 1024,
  XL: 1280,
  XXL: 1536
} as const

// Animation easing functions
export const EASING = {
  LINEAR: 'linear',
  EASE: 'ease',
  EASE_IN: 'ease-in',
  EASE_OUT: 'ease-out',
  EASE_IN_OUT: 'ease-in-out',
  BOUNCE: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)'
} as const
