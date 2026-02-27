import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/launcher' },
    { path: '/launcher', name: 'launcher', component: () => import('@/views/Launcher/index.vue') },
    { path: '/dashboard', name: 'dashboard', component: () => import('@/views/Dashboard/index.vue') },
    { path: '/overview', name: 'overview', component: () => import('@/views/Overview/index.vue') },
    { path: '/settings', name: 'settings', component: () => import('@/views/Settings/index.vue') },
    { path: '/flow', name: 'flow', component: () => import('@/views/FlowEditor/index.vue') },
    { path: '/recorder', name: 'recorder', component: () => import('@/views/Recorder/index.vue') },
    { path: '/script-editor', name: 'script-editor', component: () => import('@/views/ScriptEditor/index.vue') },
  ]
})

export default router
