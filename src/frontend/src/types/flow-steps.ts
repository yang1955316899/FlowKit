/**
 * Comprehensive FlowStep type definitions
 * Defines all 13 step types used in FlowKit automation
 */

// Base interface for all flow steps
export interface BaseFlowStep {
  type: string
}

// 1. Delay Step - 延迟
export interface DelayStep extends BaseFlowStep {
  type: 'delay'
  duration: number // milliseconds
}

// 2. Keys Step - 按键
export interface KeysStep extends BaseFlowStep {
  type: 'keys'
  keys: string // e.g., "ctrl+c", "alt+tab"
}

// 3. Type Text Step - 输入文本
export interface TypeTextStep extends BaseFlowStep {
  type: 'type_text'
  text: string
  interval?: number // milliseconds between keystrokes
}

// 4. App Step - 启动应用
export interface AppStep extends BaseFlowStep {
  type: 'app'
  path: string // application path
  args?: string // command line arguments
}

// 5. Shell Step - Shell 命令
export interface ShellStep extends BaseFlowStep {
  type: 'shell'
  command: string
  workdir?: string // working directory
}

// 6. URL Step - 打开 URL
export interface UrlStep extends BaseFlowStep {
  type: 'url'
  url: string
}

// 7. Snippet Step - 代码片段
export interface SnippetStep extends BaseFlowStep {
  type: 'snippet'
  content: string
}

// 8. Toast Step - Toast 提示
export interface ToastStep extends BaseFlowStep {
  type: 'toast'
  message: string
  level?: 'info' | 'success' | 'warning' | 'error'
  duration?: number // milliseconds
}

// 9. Mouse Click Step - 鼠标点击
export interface MouseClickStep extends BaseFlowStep {
  type: 'mouse_click'
  x: number
  y: number
  button?: 'left' | 'right' | 'middle'
  clicks?: number // single, double, triple click
}

// 10. Mouse Move Step - 鼠标移动
export interface MouseMoveStep extends BaseFlowStep {
  type: 'mouse_move'
  x: number
  y: number
  duration?: number // milliseconds for smooth movement
}

// 11. Set Variable Step - 设置变量
export interface SetVarStep extends BaseFlowStep {
  type: 'set_var'
  name: string
  value: string | number | boolean
}

// 12. HTTP Request Step - HTTP 请求
export interface HttpRequestStep extends BaseFlowStep {
  type: 'http_request'
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  url: string
  headers?: Record<string, string>
  body?: string | Record<string, unknown>
  timeout?: number // milliseconds
  saveAs?: string // variable name to save response
}

// 13. Conditional Step - 条件判断 (if needed in future)
export interface ConditionalStep extends BaseFlowStep {
  type: 'conditional'
  condition: string // expression to evaluate
  thenSteps: FlowStep[]
  elseSteps?: FlowStep[]
}

// Discriminated union of all step types
export type FlowStep =
  | DelayStep
  | KeysStep
  | TypeTextStep
  | AppStep
  | ShellStep
  | UrlStep
  | SnippetStep
  | ToastStep
  | MouseClickStep
  | MouseMoveStep
  | SetVarStep
  | HttpRequestStep
  | ConditionalStep

// Type guard functions for runtime type checking
export function isDelayStep(step: FlowStep): step is DelayStep {
  return step.type === 'delay'
}

export function isKeysStep(step: FlowStep): step is KeysStep {
  return step.type === 'keys'
}

export function isTypeTextStep(step: FlowStep): step is TypeTextStep {
  return step.type === 'type_text'
}

export function isAppStep(step: FlowStep): step is AppStep {
  return step.type === 'app'
}

export function isShellStep(step: FlowStep): step is ShellStep {
  return step.type === 'shell'
}

export function isUrlStep(step: FlowStep): step is UrlStep {
  return step.type === 'url'
}

export function isSnippetStep(step: FlowStep): step is SnippetStep {
  return step.type === 'snippet'
}

export function isToastStep(step: FlowStep): step is ToastStep {
  return step.type === 'toast'
}

export function isMouseClickStep(step: FlowStep): step is MouseClickStep {
  return step.type === 'mouse_click'
}

export function isMouseMoveStep(step: FlowStep): step is MouseMoveStep {
  return step.type === 'mouse_move'
}

export function isSetVarStep(step: FlowStep): step is SetVarStep {
  return step.type === 'set_var'
}

export function isHttpRequestStep(step: FlowStep): step is HttpRequestStep {
  return step.type === 'http_request'
}

export function isConditionalStep(step: FlowStep): step is ConditionalStep {
  return step.type === 'conditional'
}

// Helper to get step display name
export function getStepDisplayName(step: FlowStep): string {
  const names: Record<FlowStep['type'], string> = {
    delay: '延迟',
    keys: '按键',
    type_text: '输入文本',
    app: '启动应用',
    shell: 'Shell命令',
    url: '打开URL',
    snippet: '代码片段',
    toast: 'Toast提示',
    mouse_click: '鼠标点击',
    mouse_move: '鼠标移动',
    set_var: '设置变量',
    http_request: 'HTTP请求',
    conditional: '条件判断'
  }
  return names[step.type] || step.type
}
