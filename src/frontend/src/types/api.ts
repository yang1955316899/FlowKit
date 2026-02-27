export interface ApiResponse<T> {
  code: number
  data: T
  error: string
}

export interface ApiError {
  code: number
  error: string
}
