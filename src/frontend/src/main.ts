import { createApp } from 'vue'
import { pinia } from './stores'
import router from './router'
import App from './App.vue'
import './assets/styles/base.css'

const app = createApp(App)

// 全局错误处理
app.config.errorHandler = (err, instance, info) => {
  console.error('[Global Error]', err)
  console.error('[Component]', instance)
  console.error('[Error Info]', info)

  // 可以在这里集成错误上报服务
  // 例如: Sentry.captureException(err)
}

// 全局警告处理（开发环境）
app.config.warnHandler = (msg, instance, trace) => {
  console.warn('[Global Warning]', msg)
  console.warn('[Trace]', trace)
}

app.use(pinia)
app.use(router)

app.mount('#app')
