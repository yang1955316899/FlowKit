/**
 * Debounce and throttle utility functions
 */

/**
 * Creates a debounced function that delays invoking func until after wait milliseconds
 * have elapsed since the last time the debounced function was invoked.
 *
 * @param func - The function to debounce
 * @param wait - The number of milliseconds to delay
 * @returns The debounced function
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  return function debounced(...args: Parameters<T>) {
    if (timeoutId !== null) {
      clearTimeout(timeoutId)
    }

    timeoutId = setTimeout(() => {
      func(...args)
      timeoutId = null
    }, wait)
  }
}

/**
 * Creates a throttled function that only invokes func at most once per every wait milliseconds.
 *
 * @param func - The function to throttle
 * @param wait - The number of milliseconds to throttle invocations to
 * @returns The throttled function
 */
export function throttle<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let lastCallTime = 0
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  return function throttled(...args: Parameters<T>) {
    const now = Date.now()
    const timeSinceLastCall = now - lastCallTime

    if (timeSinceLastCall >= wait) {
      // Enough time has passed, call immediately
      lastCallTime = now
      func(...args)
    } else {
      // Schedule a call for later
      if (timeoutId !== null) {
        clearTimeout(timeoutId)
      }

      timeoutId = setTimeout(() => {
        lastCallTime = Date.now()
        func(...args)
        timeoutId = null
      }, wait - timeSinceLastCall)
    }
  }
}

/**
 * Creates a debounced function with a leading edge option.
 * The function is invoked on the leading edge if leading is true,
 * and on the trailing edge if trailing is true.
 *
 * @param func - The function to debounce
 * @param wait - The number of milliseconds to delay
 * @param options - Options object
 * @returns The debounced function
 */
export function debounceWithOptions<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number,
  options: { leading?: boolean; trailing?: boolean } = {}
): (...args: Parameters<T>) => void {
  const { leading = false, trailing = true } = options
  let timeoutId: ReturnType<typeof setTimeout> | null = null
  let lastCallTime = 0

  return function debounced(...args: Parameters<T>) {
    const now = Date.now()
    const isFirstCall = lastCallTime === 0

    if (timeoutId !== null) {
      clearTimeout(timeoutId)
    }

    if (leading && isFirstCall) {
      func(...args)
      lastCallTime = now
    }

    if (trailing) {
      timeoutId = setTimeout(() => {
        if (!leading || !isFirstCall) {
          func(...args)
        }
        lastCallTime = 0
        timeoutId = null
      }, wait)
    }
  }
}
