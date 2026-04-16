<template>
  <div :class="{ dark: ui.theme === 'dark' }" class="min-h-screen flex flex-col
       bg-[var(--color-bg)] text-[var(--color-text)]">
    <Navbar />
    <TopicDrawer />
    <main class="flex-1 overflow-y-auto pb-16 pt-0">
      <RouterView />
    </main>
    <BottomTabBar />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import Navbar from './components/layout/Navbar.vue'
import BottomTabBar from './components/layout/BottomTabBar.vue'
import TopicDrawer from './components/layout/TopicDrawer.vue'
import { useUiStore } from './stores/ui.js'
import { useTopicsStore } from './stores/topics.js'

const ui = useUiStore()
const topics = useTopicsStore()
onMounted(() => topics.loadTopics())
</script>
