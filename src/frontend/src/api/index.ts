import type { ApiResponse } from '@/types/api'
import { NetworkError, TimeoutError } from '@/utils/error'
import { API_CONFIG } from '@/constants'

const API_BASE = '/api/v1'

interface CacheEntry<T> {
  data: T
  timestamp: number
}

class ApiClient {
  private timeout = API_CONFIG.TIMEOUT
  private maxRetries = API_CONFIG.RETRY_COUNT
  private cache = new Map<string, CacheEntry<unknown>>()
  private cacheTTL = 5000 // 5秒缓存
  private pendingRequests = new Map<string, AbortController>() // 跟踪进行中的请求

  private getCacheKey(method: string, path: string): string {
    return `${method}:${path}`
  }

  private getCache<T>(key: string): T | null {
    const cached = this.cache.get(key)
    if (cached && Date.now() - cached.timestamp < this.cacheTTL) {
      return cached.data
    }
    this.cache.delete(key)
    return null
  }

  private setCache<T>(key: string, data: T): void {
    this.cache.set(key, { data, timestamp: Date.now() })
  }

  public clearCache(pattern?: string): void {
    if (!pattern) {
      this.cache.clear()
      return
    }
    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        this.cache.delete(key)
      }
    }
  }

  private async request<T>(
    method: string,
    path: string,
    body?: any,
    retries = 0
  ): Promise<T> {
    const url = `${API_BASE}${path}`
    const requestKey = `${method}:${path}`

    // 取消之前相同的请求
    const existingController = this.pendingRequests.get(requestKey)
    if (existingController) {
      existingController.abort()
    }

    const controller = new AbortController()
    this.pendingRequests.set(requestKey, controller)

    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    try {
      const options: RequestInit = {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        signal: controller.signal
      }

      if (body) {
        options.body = JSON.stringify(body)
      }

      const response = await fetch(url, options)
      clearTimeout(timeoutId)
      this.pendingRequests.delete(requestKey)

      // 重试逻辑（仅针对网络错误或 5xx 错误）
      if (!response.ok && response.status >= 500 && retries < this.maxRetries) {
        const delay = API_CONFIG.RETRY_DELAY * Math.pow(2, retries) // 指数退避
        await new Promise(resolve => setTimeout(resolve, delay))
        return this.request<T>(method, path, body, retries + 1)
      }

      const data: ApiResponse<T> = await response.json()

      if (data.code !== 0) {
        throw new Error(data.error || 'API request failed')
      }

      return data.data
    } catch (error: unknown) {
      clearTimeout(timeoutId)
      this.pendingRequests.delete(requestKey)

      if (error instanceof Error && error.name === 'AbortError') {
        throw new TimeoutError('请求超时，请检查网络连接')
      }

      // 网络错误重试
      if (retries < this.maxRetries && error instanceof Error && error.message.includes('fetch')) {
        const delay = API_CONFIG.RETRY_DELAY * Math.pow(2, retries)
        await new Promise(resolve => setTimeout(resolve, delay))
        return this.request<T>(method, path, body, retries + 1)
      }

      // Wrap network errors
      if (error instanceof Error && (error.message.includes('fetch') || error.message.includes('network'))) {
        throw new NetworkError('网络连接失败，请检查网络设置')
      }

      throw error
    }
  }

  async get<T>(path: string, useCache = true): Promise<T> {
    const cacheKey = this.getCacheKey('GET', path)

    if (useCache) {
      const cached = this.getCache<T>(cacheKey)
      if (cached !== null) {
        return cached
      }
    }

    const data = await this.request<T>('GET', path)

    if (useCache) {
      this.setCache(cacheKey, data)
    }

    return data
  }

  async post<T>(path: string, body?: any): Promise<T> {
    const data = await this.request<T>('POST', path, body)
    // POST 请求后清除相关缓存
    this.clearCache(path.split('/')[1]) // 清除同一资源的缓存
    return data
  }

  async put<T>(path: string, body?: any): Promise<T> {
    const data = await this.request<T>('PUT', path, body)
    // PUT 请求后清除相关缓存
    this.clearCache(path.split('/')[1])
    return data
  }

  async delete<T>(path: string): Promise<T> {
    const data = await this.request<T>('DELETE', path)
    // DELETE 请求后清除相关缓存
    this.clearCache(path.split('/')[1])
    return data
  }

  /**
   * 取消所有进行中的请求
   */
  cancelAll(): void {
    for (const controller of this.pendingRequests.values()) {
      controller.abort()
    }
    this.pendingRequests.clear()
  }

  /**
   * 取消特定路径的请求
   */
  cancel(path: string): void {
    for (const [key, controller] of this.pendingRequests.entries()) {
      if (key.includes(path)) {
        controller.abort()
        this.pendingRequests.delete(key)
      }
    }
  }
}

export const api = new ApiClient()

