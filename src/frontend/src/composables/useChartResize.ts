/**
 * ECharts resize handling composable
 * Automatically resizes charts when container size changes
 */

import { onMounted, onUnmounted, type Ref } from 'vue'
import type { ECharts } from 'echarts'

export function useChartResize(chartRef: Ref<ECharts | null>, containerRef: Ref<HTMLElement | null>) {
  let resizeObserver: ResizeObserver | null = null

  const handleResize = () => {
    if (chartRef.value) {
      chartRef.value.resize()
    }
  }

  onMounted(() => {
    if (!containerRef.value) return

    // Use ResizeObserver for better performance
    resizeObserver = new ResizeObserver(() => {
      handleResize()
    })

    resizeObserver.observe(containerRef.value)

    // Also listen to window resize as fallback
    window.addEventListener('resize', handleResize)
  })

  onUnmounted(() => {
    if (resizeObserver && containerRef.value) {
      resizeObserver.unobserve(containerRef.value)
      resizeObserver.disconnect()
    }

    window.removeEventListener('resize', handleResize)
  })

  return {
    handleResize
  }
}
