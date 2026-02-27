/**
 * Error handling utility functions
 */

import type { Result, AsyncResult } from '@/types/common'

/**
 * Wraps a function to return a Result type instead of throwing
 *
 * @param func - The function to wrap
 * @returns A function that returns Result<T, E>
 */
export function wrapResult<T, E = Error>(
  func: () => T
): Result<T, E> {
  try {
    const value = func()
    return { ok: true, value }
  } catch (error) {
    return { ok: false, error: error as E }
  }
}

/**
 * Wraps an async function to return an AsyncResult type instead of throwing
 *
 * @param func - The async function to wrap
 * @returns A function that returns AsyncResult<T, E>
 */
export async function wrapAsyncResult<T, E = Error>(
  func: () => Promise<T>
): AsyncResult<T, E> {
  try {
    const value = await func()
    return { ok: true, value }
  } catch (error) {
    return { ok: false, error: error as E }
  }
}

/**
 * Extracts a user-friendly error message from various error types
 *
 * @param error - The error to extract message from
 * @returns User-friendly error message
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }

  if (typeof error === 'string') {
    return error
  }

  if (error && typeof error === 'object' && 'message' in error) {
    return String(error.message)
  }

  return '未知错误'
}

/**
 * Checks if an error is a network error
 *
 * @param error - The error to check
 * @returns True if it's a network error
 */
export function isNetworkError(error: unknown): boolean {
  if (error instanceof Error) {
    return (
      error.message.includes('network') ||
      error.message.includes('fetch') ||
      error.message.includes('timeout') ||
      error.name === 'NetworkError' ||
      error.name === 'TypeError'
    )
  }

  return false
}

/**
 * Checks if an error is a timeout error
 *
 * @param error - The error to check
 * @returns True if it's a timeout error
 */
export function isTimeoutError(error: unknown): boolean {
  if (error instanceof Error) {
    return (
      error.message.includes('timeout') ||
      error.message.includes('timed out') ||
      error.name === 'TimeoutError'
    )
  }

  return false
}

/**
 * Checks if an error is an abort error
 *
 * @param error - The error to check
 * @returns True if it's an abort error
 */
export function isAbortError(error: unknown): boolean {
  if (error instanceof Error) {
    return error.name === 'AbortError'
  }

  return false
}

/**
 * Creates a custom error class
 *
 * @param name - The error name
 * @param message - The error message
 * @returns Custom error instance
 */
export class AppError extends Error {
  constructor(
    message: string,
    public code?: string,
    public details?: Record<string, unknown>
  ) {
    super(message)
    this.name = 'AppError'
  }
}

/**
 * Creates a network error
 *
 * @param message - The error message
 * @returns Network error instance
 */
export class NetworkError extends AppError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, 'NETWORK_ERROR', details)
    this.name = 'NetworkError'
  }
}

/**
 * Creates a timeout error
 *
 * @param message - The error message
 * @returns Timeout error instance
 */
export class TimeoutError extends AppError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, 'TIMEOUT_ERROR', details)
    this.name = 'TimeoutError'
  }
}

/**
 * Creates a validation error
 *
 * @param message - The error message
 * @returns Validation error instance
 */
export class ValidationError extends AppError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, 'VALIDATION_ERROR', details)
    this.name = 'ValidationError'
  }
}

/**
 * Retries a function with exponential backoff
 *
 * @param func - The function to retry
 * @param maxRetries - Maximum number of retries
 * @param baseDelay - Base delay in milliseconds
 * @returns The result of the function
 */
export async function retryWithBackoff<T>(
  func: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  let lastError: unknown

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await func()
    } catch (error) {
      lastError = error

      // Don't retry on abort errors
      if (isAbortError(error)) {
        throw error
      }

      // Don't retry if this was the last attempt
      if (attempt === maxRetries) {
        break
      }

      // Calculate delay with exponential backoff
      const delay = baseDelay * Math.pow(2, attempt)
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }

  throw lastError
}

/**
 * Creates a safe version of a function that catches errors and returns a default value
 *
 * @param func - The function to make safe
 * @param defaultValue - The default value to return on error
 * @returns Safe function
 */
export function safe<T, Args extends unknown[]>(
  func: (...args: Args) => T,
  defaultValue: T
): (...args: Args) => T {
  return (...args: Args) => {
    try {
      return func(...args)
    } catch {
      return defaultValue
    }
  }
}

/**
 * Creates a safe async version of a function that catches errors and returns a default value
 *
 * @param func - The async function to make safe
 * @param defaultValue - The default value to return on error
 * @returns Safe async function
 */
export function safeAsync<T, Args extends unknown[]>(
  func: (...args: Args) => Promise<T>,
  defaultValue: T
): (...args: Args) => Promise<T> {
  return async (...args: Args) => {
    try {
      return await func(...args)
    } catch {
      return defaultValue
    }
  }
}
