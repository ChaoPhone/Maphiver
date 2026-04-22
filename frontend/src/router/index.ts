import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/Home.vue'),
    },
    {
      path: '/read/:sessionId?',
      name: 'read',
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