<template>
  <div class="dashboard">
    <!-- Token 选择 pills -->
    <div v-if="tokens.length > 1" class="token-tabs">
      <button
        v-for="(tok, i) in tokens"
        :key="i"
        :class="['token-pill', { active: selectedIdx === i }]"
        @click="selectToken(i)"
      >
        {{ tok.name?.slice(0, 5) || 'T' + (i+1) }}
      </button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-else-if="stats">
      <!-- 指标行 2x2 -->
      <div class="metrics">
        <div class="metric">
          <span class="m-val">{{ stats.requests_today }}</span>
          <span class="m-label">今日请求</span>
        </div>
        <div class="metric">
          <span class="m-val">{{ formatNum(stats.tokens_today) }}</span>
          <span class="m-label">Tokens</span>
        </div>
        <div class="metric">
          <span class="m-val">${{ stats.cost_today?.toFixed(2) || '0.00' }}</span>
          <span class="m-label">费用</span>
        </div>
        <div class="metric">
          <span class="m-val">{{ stats.remaining_days }}</span>
          <span class="m-label">剩余天数</span>
        </div>
      </div>

      <!-- 详情卡片 -->
      <div class="detail-card">
        <div class="d-row">
          <span>总请求</span>
          <span class="d-val">{{ stats.total_requests }}</span>
        </div>
        <div class="d-row">
          <span>总 Tokens</span>
          <span class="d-val">{{ formatNum(stats.total_tokens) }}</span>
        </div>
        <div class="d-row">
          <span>总费用</span>
          <span class="d-val">${{ stats.total_cost?.toFixed(2) || '0.00' }}</span>
        </div>
        <div class="d-row">
          <span>每日限额</span>
          <span class="d-val">{{ stats.daily_limit || '--' }}</span>
        </div>
        <div class="d-row">
          <span>到期日期</span>
          <span class="d-val">{{ stats.expire_date || '--' }}</span>
        </div>
      </div>

      <!-- 图表 -->
      <div class="chart-card">
        <div ref="chartRef" class="chart" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import * as echarts from 'echarts'

const store = useDashboardStore()
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const tokens = computed(() => store.tokens)
const selectedIdx = ref(0)
const stats = computed(() => store.stats)
const details = computed(() => store.details)
const loading = computed(() => store.loading)

const formatNum = (n: number) => n >= 1000 ? (n / 1000).toFixed(1) + 'k' : String(n || 0)

const selectToken = (i: number) => {
  selectedIdx.value = i
  store.selectToken(i)
}

const initChart = () => {
  if (!chartRef.value || !details.value?.length) return
  if (!chart) chart = echarts.init(chartRef.value)

  chart.setOption({
    backgroundColor: 'transparent',
    grid: { top: 10, right: 10, bottom: 24, left: 36 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: details.value.map(d => d.date),
      axisLabel: { fontSize: 9, color: '#6c7086' },
      axisLine: { lineStyle: { color: '#252538' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { fontSize: 9, color: '#6c7086' },
      splitLine: { lineStyle: { color: '#252538' } },
    },
    series: [{
      type: 'line',
      data: details.value.map(d => d.requests),
      smooth: true,
      itemStyle: { color: '#89b4fa' },
      areaStyle: { color: 'rgba(137,180,250,0.15)' },
      lineStyle: { width: 2 },
      symbolSize: 4,
    }]
  })
}

watch(details, () => nextTick(initChart))

onMounted(async () => {
  await store.fetchTokens()
  if (tokens.value.length) {
    await store.selectToken(0)
    nextTick(initChart)
  }
  store.startAutoRefresh()
})

onUnmounted(() => {
  store.stopAutoRefresh()
  chart?.dispose()
})
</script>

<style scoped>
.dashboard {
  flex: 1;
  padding: 6px 10px;
  overflow-y: auto;
}

.token-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 8px;
}

.token-pill {
  padding: 3px 10px;
  border-radius: 11px;
  font-size: 11px;
  background: var(--card2);
  color: var(--dim);
  transition: all 0.15s;
}
.token-pill.active {
  background: var(--accent);
  color: #fff;
  font-weight: 600;
}

.loading { text-align: center; padding: 30px; color: var(--dim); font-size: 12px; }

.metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  margin-bottom: 8px;
}

.metric {
  background: var(--card);
  border-radius: 8px;
  padding: 10px;
  text-align: center;
}

.m-val {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: var(--accent);
  font-family: var(--mono);
}

.m-label {
  font-size: 10px;
  color: var(--dim);
  margin-top: 2px;
}

.detail-card {
  background: var(--card);
  border-radius: 8px;
  padding: 8px 14px;
  margin-bottom: 8px;
}

.d-row {
  display: flex;
  justify-content: space-between;
  padding: 5px 0;
  font-size: 11px;
  border-bottom: 1px solid var(--border-subtle);
}
.d-row:last-child { border-bottom: none; }
.d-row span:first-child { color: var(--sub); }
.d-val { font-family: var(--mono); font-weight: 500; }

.chart-card {
  background: var(--card);
  border-radius: 8px;
  padding: 8px;
}

.chart { width: 100%; height: 180px; }
</style>
