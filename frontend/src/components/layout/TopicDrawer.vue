<template>
  <Transition name="fade">
    <div v-if="ui.drawerOpen"
         class="fixed inset-0 z-50 bg-black/40"
         @click="ui.closeDrawer()" />
  </Transition>
  <Transition name="slide">
    <aside v-if="ui.drawerOpen"
           class="fixed top-0 left-0 bottom-0 z-50 w-72
                  bg-[var(--color-surface)] border-r border-[var(--color-border)]
                  overflow-y-auto flex flex-col">
      <div class="flex items-center justify-between p-4 border-b border-[var(--color-border)]">
        <span class="font-bold text-lg">Temari</span>
        <button @click="ui.closeDrawer()" class="text-2xl p-1">✕</button>
      </div>
      <section class="p-2">
        <p class="text-xs font-semibold uppercase text-gray-400 px-2 py-1">Bloc General</p>
        <TopicItem v-for="t in topics.generalTopics" :key="t.id" :topic="t"
                   @select="selectTopic(t.id)" />
      </section>
      <section class="p-2">
        <p class="text-xs font-semibold uppercase text-gray-400 px-2 py-1">Bloc Específic</p>
        <TopicItem v-for="t in topics.especificTopics" :key="t.id" :topic="t"
                   @select="selectTopic(t.id)" />
      </section>
    </aside>
  </Transition>
</template>

<script setup>
import { useUiStore } from '../../stores/ui.js'
import { useTopicsStore } from '../../stores/topics.js'
import { useRouter } from 'vue-router'

const ui = useUiStore()
const topics = useTopicsStore()
const router = useRouter()

function selectTopic(id) {
  topics.setActiveTopic(id)
  ui.closeDrawer()
  router.push('/apunts')
}
</script>

<script>
import { useTopicsStore } from '../../stores/topics.js'

const TopicItem = {
  props: ['topic'],
  emits: ['select'],
  template: `
    <button @click="$emit('select')"
      class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-sm
             hover:bg-primary/10 transition-colors"
      :class="{ 'bg-primary/10 text-primary font-medium': isActive }">
      <span class="text-base" :title="progressLabel">{{ dot }}</span>
      <span class="truncate">Tema {{ topic.number }}: {{ topic.title }}</span>
    </button>
  `,
  computed: {
    isActive() {
      return useTopicsStore().activeTopicId === this.topic.id
    },
    dot() {
      const p = this.topic.overall_pct
      if (p >= 80) return '✓'
      if (p >= 40) return '◑'
      return '○'
    },
    progressLabel() { return `${Math.round(this.topic.overall_pct)}%` }
  }
}
export default { components: { TopicItem } }
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.slide-enter-active, .slide-leave-active { transition: transform 0.25s ease; }
.slide-enter-from, .slide-leave-to { transform: translateX(-100%); }
</style>
