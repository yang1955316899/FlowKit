import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import compression from 'vite-plugin-compression'
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig(({ mode }) => ({
  plugins: [
    vue(),
    // Gzip 压缩
    compression({
      algorithm: 'gzip',
      ext: '.gz',
      threshold: 10240, // 只压缩大于 10KB 的文件
      deleteOriginFile: false
    }),
    // Bundle 分析（仅在 analyze 模式下）
    mode === 'analyze' && visualizer({
      open: true,
      filename: 'dist/stats.html',
      gzipSize: true,
      brotliSize: true
    })
  ].filter(Boolean),
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  base: '/',
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:18900',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: '../web/static',
    emptyOutDir: true,
    assetsDir: 'assets',
    // 生产环境优化
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: mode === 'production', // 生产环境移除 console
        drop_debugger: true,
        pure_funcs: mode === 'production' ? ['console.log', 'console.info'] : []
      }
    },
    // 代码分割优化
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['vue', 'vue-router', 'pinia'],
          'utils': ['@vueuse/core'],
          'echarts': ['echarts']
        },
        // 优化文件名
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]'
      }
    },
    // 提高 chunk 大小警告阈值
    chunkSizeWarningLimit: 1000
  }
}))

