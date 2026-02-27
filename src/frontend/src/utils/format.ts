/**
 * Formatting utility functions
 */

import { TEXT_CONFIG } from '@/constants'

/**
 * Formats a number with K/M/B suffixes for large numbers
 *
 * @param num - The number to format
 * @returns Formatted string (e.g., "1.2K", "3.4M")
 */
export function formatNumber(num: number): string {
  if (num < 1000) {
    return num.toString()
  }

  if (num < 1_000_000) {
    return (num / 1000).toFixed(1).replace(/\.0$/, '') + 'K'
  }

  if (num < 1_000_000_000) {
    return (num / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M'
  }

  return (num / 1_000_000_000).toFixed(1).replace(/\.0$/, '') + 'B'
}

/**
 * Formats a number as currency (CNY)
 *
 * @param amount - The amount to format
 * @param currency - Currency symbol (default: '¥')
 * @returns Formatted currency string
 */
export function formatCurrency(amount: number, currency = '¥'): string {
  return `${currency}${amount.toFixed(2)}`
}

/**
 * Truncates text to a maximum length, considering Chinese characters as double width
 *
 * @param text - The text to truncate
 * @param maxLength - Maximum length in characters
 * @param suffix - Suffix to append when truncated (default: '...')
 * @returns Truncated text
 */
export function truncateText(
  text: string,
  maxLength: number = TEXT_CONFIG.MAX_LABEL_LENGTH,
  suffix: string = TEXT_CONFIG.TRUNCATE_SUFFIX
): string {
  if (!text) return ''

  let length = 0
  let truncateIndex = 0

  for (let i = 0; i < text.length; i++) {
    const char = text[i]
    // Chinese characters, Japanese, Korean count as 2 width
    const charWidth = /[\u4e00-\u9fa5\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]/.test(char) ? 2 : 1
    length += charWidth

    if (length > maxLength) {
      truncateIndex = i
      break
    }
  }

  if (truncateIndex === 0) {
    return text
  }

  return text.slice(0, truncateIndex) + suffix
}

/**
 * Formats a date to a readable string
 *
 * @param date - The date to format
 * @param format - Format type ('short', 'long', 'time')
 * @returns Formatted date string
 */
export function formatDate(
  date: Date | string | number,
  format: 'short' | 'long' | 'time' = 'short'
): string {
  const d = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date

  if (isNaN(d.getTime())) {
    return 'Invalid Date'
  }

  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')

  switch (format) {
    case 'short':
      return `${year}-${month}-${day}`
    case 'long':
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
    case 'time':
      return `${hours}:${minutes}:${seconds}`
    default:
      return `${year}-${month}-${day}`
  }
}

/**
 * Formats a duration in milliseconds to a readable string
 *
 * @param ms - Duration in milliseconds
 * @returns Formatted duration string (e.g., "1h 23m", "45s")
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`
  }

  const seconds = Math.floor(ms / 1000)
  if (seconds < 60) {
    return `${seconds}s`
  }

  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (minutes < 60) {
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`
  }

  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`
}

/**
 * Formats file size in bytes to a readable string
 *
 * @param bytes - Size in bytes
 * @returns Formatted size string (e.g., "1.2 KB", "3.4 MB")
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`
  }

  if (bytes < 1024 * 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

/**
 * Capitalizes the first letter of a string
 *
 * @param str - The string to capitalize
 * @returns Capitalized string
 */
export function capitalize(str: string): string {
  if (!str) return ''
  return str.charAt(0).toUpperCase() + str.slice(1)
}

/**
 * Converts a string to kebab-case
 *
 * @param str - The string to convert
 * @returns Kebab-cased string
 */
export function kebabCase(str: string): string {
  return str
    .replace(/([a-z])([A-Z])/g, '$1-$2')
    .replace(/[\s_]+/g, '-')
    .toLowerCase()
}

/**
 * Converts a string to camelCase
 *
 * @param str - The string to convert
 * @returns CamelCased string
 */
export function camelCase(str: string): string {
  return str
    .replace(/[-_\s]+(.)?/g, (_, char) => (char ? char.toUpperCase() : ''))
    .replace(/^[A-Z]/, (char) => char.toLowerCase())
}
