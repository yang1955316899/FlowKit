/**
 * Common type definitions used across the application
 */

// Result type for error handling (Rust-style)
export type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E }

// Async result type
export type AsyncResult<T, E = Error> = Promise<Result<T, E>>

// Paginated response type
export interface PaginatedResponse<T> {
  items: T[]
  page: number
  pageSize: number
  total: number
  totalPages: number
}

// Sort parameters
export interface SortParams {
  field: string
  order: 'asc' | 'desc'
}

// Filter parameters
export interface FilterParams {
  [key: string]: string | number | boolean | undefined
}

// Query parameters combining pagination, sorting, and filtering
export interface QueryParams {
  page?: number
  pageSize?: number
  sort?: SortParams
  filters?: FilterParams
}

// API error response
export interface ApiError {
  message: string
  code?: string
  details?: Record<string, unknown>
}

// Loading state
export interface LoadingState {
  isLoading: boolean
  message?: string
}

// Network status
export interface NetworkStatus {
  online: boolean
  lastChecked: Date
}

// Validation result
export interface ValidationResult {
  valid: boolean
  errors: string[]
}

// Generic ID type
export type ID = string | number

// Timestamp type
export type Timestamp = number | string | Date

// Optional type helper
export type Optional<T> = T | undefined

// Nullable type helper
export type Nullable<T> = T | null

// Deep partial type helper
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

// Pick by value type helper
export type PickByValue<T, V> = Pick<T, {
  [K in keyof T]: T[K] extends V ? K : never
}[keyof T]>

// Omit by value type helper
export type OmitByValue<T, V> = Omit<T, {
  [K in keyof T]: T[K] extends V ? K : never
}[keyof T]>
