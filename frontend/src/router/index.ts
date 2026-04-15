import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'read',
      component: () => import('@/views/Read.vue'),
    },
    {
      path: '/read/:sessionId',
      name: 'read-session',
      component: () => import('@/views/Read.vue'),
    },
    {
      path: '/history',
      name: 'history',
      component: () => import('@/views/Home.vue'),
    },
  ],
})

export default router