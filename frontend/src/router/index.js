import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/apunts' },
  { path: '/apunts', component: () => import('../views/ApuntsView.vue') },
  { path: '/flash', component: () => import('../views/FlashcardsView.vue') },
  { path: '/practica', component: () => import('../views/PracticaView.vue') },
  { path: '/progres', component: () => import('../views/ProgresView.vue') },
  { path: '/config', component: () => import('../views/SettingsView.vue') },
]

export default createRouter({ history: createWebHistory(), routes })
