<template>
  <div class="overview">
    <div v-for="(token, i) in tokens" :key="i" class="token-card">
      <!-- 删除确认 -->
      <div v-if="deleteConfirm === i" class="del-confirm">
        <span class="del-text">删除 {{ token.name }}?</span>
        <div class="del-actions">
          <button class="del-ok" @click="confirmDelete(i)">确定</button>
          <button class="del-cancel" @click="deleteConfirm = null">取消</button>
        </div>
      </div>

      <!-- 正常卡片 -->
      <template v-else>
        <div class="token-row1">
          <span :class="['status-dot', daysColor(token.days)]" />
          <span class="token-name" @click="goDetail(i)">{{ token.name }}</span>
          <span :class="['days-pill', daysColor(token.days)]">{{ token.days }}d</span>
          <button class="icon-btn" @click="editToken(i)" title="编辑">✎</button>
          <button class="icon-btn" @click="deleteConfirm = i" title="删除">×</button>
        </div>

        <!-- 进度条 -->
        <div v-if="token.limit > 0" class="progress-section">
          <div class="progress-bar">
            <div
              class="progress-fill"
              :style="{ width: pct(token) + '%' }"
              :class="barColor(token)"
            />
          </div>
          <div class="cost-row">
            <span class="cost-val">{{ token.cost }}</span>
            <span class="cost-limit">/ ${{ token.limit }}</span>
          </div>
          <span class="expire-text">{{ token.expire }}</span>
        </div>

        <div v-else class="simple-row">
          <span class="cost-accent">{{ token.cost }}</span>
          <span class="expire-dim">{{ token.expire }}</span>
        </div>
      </template>
    </div>

    <!-- 添加按钮 -->
    <div class="add-btn" @click="addToken">+  添加 Token</div>

    <!-- Token 编辑模态框 -->
    <TokenModal
      :show="modal.show"
      :token="modal.token"
      @close="modal.show = false"
      @save="handleSave"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useOverviewStore } from '@/stores/overview'
import { useToast } from '@/composables/useToast'
import type { Token } from '@/types/token'
import TokenModal from './TokenModal.vue'

const store = useOverviewStore()
const { success, error } = useToast()
const deleteConfirm = ref<number | null>(null)

const tokens = ref<any[]>([])

const modal = reactive({
  show: false,
  token: null as Token | null
})

const fetchTokens = async () => {
  await store.fetchTokens()
  tokens.value = store.tokens
}

const daysColor = (days: number) =>
  days > 14 ? 'green' : days > 7 ? 'yellow' : 'red'

const pct = (t: any) => {
  const cost = parseFloat(String(t.cost).replace('$', '').replace(',', '')) || 0
  return Math.min(cost / t.limit * 100, 100)
}

const barColor = (t: any) => {
  const p = pct(t)
  return p > 90 ? 'red' : p > 70 ? 'yellow' : 'accent'
}

const goDetail = (i: number) => {
  // TODO: Navigate to dashboard with this token selected
}

const editToken = (i: number) => {
  modal.token = store.tokens[i]
  modal.show = true
}

const confirmDelete = async (i: number) => {
  try {
    await store.deleteToken(i)
    deleteConfirm.value = null
    await fetchTokens()
    success('已删除')
  } catch {
    error('删除失败')
  }
}

const addToken = () => {
  modal.token = null
  modal.show = true
}

const handleSave = async (data: Partial<Token>) => {
  try {
    if (modal.token) {
      await store.updateToken(modal.token.index, data)
      success('已更新')
    } else {
      await store.addToken(data)
      success('已添加')
    }
    modal.show = false
    await fetchTokens()
  } catch {
    error('保存失败')
  }
}

onMounted(fetchTokens)
</script>

<style scoped>
.overview {
  flex: 1;
  padding: 6px 10px;
  overflow-y: auto;
}

.token-card {
  background: var(--card);
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 8px;
}

.token-row1 {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.status-dot.green { background: var(--green); }
.status-dot.yellow { background: var(--yellow); }
.status-dot.red { background: var(--red); }

.token-name {
  flex: 1;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.days-pill {
  font-size: 10px;
  font-weight: 700;
  font-family: var(--mono);
  padding: 2px 6px;
  border-radius: 10px;
}
.days-pill.green { background: var(--green-glow); color: var(--green); }
.days-pill.yellow { background: var(--yellow-glow); color: var(--yellow); }
.days-pill.red { background: var(--red-glow); color: var(--red); }

.icon-btn {
  font-size: 14px;
  color: var(--dim);
  padding: 2px 4px;
}
.icon-btn:hover { color: var(--text); }

.progress-section { margin-top: 8px; }

.progress-bar {
  height: 14px;
  background: var(--bar-bg);
  border-radius: 7px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 7px;
  transition: width 0.3s;
}
.progress-fill.accent { background: var(--accent); }
.progress-fill.yellow { background: var(--yellow); }
.progress-fill.red { background: var(--red); }

.cost-row {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
}

.cost-val { font-size: 13px; font-weight: 700; font-family: var(--mono); }
.cost-limit { font-size: 12px; color: var(--dim); font-family: var(--mono); }
.expire-text { font-size: 10px; color: var(--dim); font-family: var(--mono); }

.simple-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 6px;
}
.cost-accent { font-size: 14px; font-weight: 700; color: var(--accent); font-family: var(--mono); }
.expire-dim { font-size: 11px; color: var(--dim); font-family: var(--mono); }

.del-confirm {
  background: var(--red-glow);
  border-radius: 10px;
  padding: 10px 14px;
}
.del-text { font-size: 12px; font-weight: 600; color: var(--red); }
.del-actions { display: flex; gap: 6px; margin-top: 8px; justify-content: flex-end; }
.del-ok {
  padding: 4px 12px; border-radius: 10px;
  background: var(--red); color: #fff;
  font-size: 11px; font-weight: 600;
}
.del-cancel {
  padding: 4px 12px; border-radius: 10px;
  background: var(--card2); color: var(--dim);
  font-size: 11px;
}

.add-btn {
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  text-align: center;
  padding: 10px;
  color: var(--dim);
  font-size: 12px;
  cursor: pointer;
  transition: border-color 0.15s;
}
.add-btn:hover { border-color: var(--accent); color: var(--accent); }
</style>
