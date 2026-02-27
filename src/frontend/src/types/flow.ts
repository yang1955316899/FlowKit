import type { FlowStep } from './flow-steps'

export interface FlowStepType {
  type: string
  name: string
  icon: string
  desc: string
  color: string
}

export interface FlowCategory {
  category: string
  steps: FlowStepType[]
}

export interface FlowExecuteRequest {
  steps: FlowStep[]
  delay: number
}
