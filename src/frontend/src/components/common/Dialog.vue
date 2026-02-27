<template>
  <teleport to="body">
    <transition name="dialog-fade">
      <div v-if="show" class="dialog-overlay" @click="handleOverlayClick">
        <div class="dialog-wrapper" @click.stop>
          <div class="dialog-container" :style="{ width: width }">
            <!-- 标题栏 -->
            <div class="dialog-header">
              <span class="dialog-title">{{ title }}</span>
              <button class="dialog-close" @click="close">×</button>
            </div>

            <!-- 内容区 -->
            <div class="dialog-body">
              <slot></slot>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  show: boolean
  title: string
  width?: string
  closeOnClickModal?: boolean
}>(), {
  width: '50%',
  closeOnClickModal: true
})

const emit = defineEmits<{
  close: []
}>()

const close = () => emit('close')

const handleOverlayClick = () => {
  if (props.closeOnClickModal) {
    close()
  }
}
</script>

<style scoped>
/* 遮罩层 */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

/* 对话框包装器 */
.dialog-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  padding: 20px;
}

/* 对话框容器 */
.dialog-container {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

/* 标题栏 */
.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-subtle);
}

.dialog-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.dialog-close {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  font-size: 24px;
  color: var(--dim);
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.dialog-close:hover {
  background: var(--btn-hover);
  color: var(--text);
}

/* 内容区 */
.dialog-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

/* 动画 */
.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.3s;
}

.dialog-fade-enter-active .dialog-container,
.dialog-fade-leave-active .dialog-container {
  transition: transform 0.3s;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}

.dialog-fade-enter-from .dialog-container,
.dialog-fade-leave-to .dialog-container {
  transform: scale(0.9);
}
</style>
