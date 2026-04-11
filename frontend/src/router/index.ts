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
      path: '/upload',
      name: 'upload',
      component: () => import('@/views/Upload.vue'),
    },
    {
      path: '/read/:sessionId',
      name: 'read',
      component: () => import('@/views/Read.vue'),
    },
  ],
})

export default router