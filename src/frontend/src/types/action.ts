export type ActionType = 'app' | 'url' | 'combo' | 'shell' | 'snippet' | 'keys' | 'script'

export interface BaseAction {
  id?: string
  index?: number
  type: ActionType
  label: string
  icon: string
  hotkey?: string
}

export interface AppAction extends BaseAction {
  type: 'app'
  target: string
}

export interface UrlAction extends BaseAction {
  type: 'url'
  target: string
}

export interface ShellAction extends BaseAction {
  type: 'shell'
  target: string
}

export interface SnippetAction extends BaseAction {
  type: 'snippet'
  target: string
}

export interface KeysAction extends BaseAction {
  type: 'keys'
  target: string
}

export interface ScriptAction extends BaseAction {
  type: 'script'
  target: string
}

export interface ComboAction extends BaseAction {
  type: 'combo'
  steps: FlowStep[]
  delay: number
}

export type Action = AppAction | UrlAction | ShellAction | SnippetAction | KeysAction | ScriptAction | ComboAction

// Import FlowStep from flow-steps.ts
export type { FlowStep } from './flow-steps'

export interface Page {
  index: number
  name: string
  actions: Action[]
}

export interface ActionsResponse {
  page: number
  pageName: string
  totalPages: number
  actions: Action[]
}

export interface SearchResult {
  page: number
  pageName: string
  index: number
  id: string
  type: ActionType
  label: string
  icon: string
}
