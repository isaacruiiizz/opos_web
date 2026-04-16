<template>
  <div>
    <div class="sticky top-0 z-30 flex items-center gap-2 px-4 py-2
                bg-[var(--color-surface)] border-b border-[var(--color-border)]">
      <button @click="mode = 'text'"
              :class="mode === 'text' ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-gray-800'"
              class="px-3 py-1.5 rounded-full text-sm font-medium transition-colors">
        ✏️ Text
      </button>
      <button @click="mode = 'draw'"
              :class="mode === 'draw' ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-gray-800'"
              class="px-3 py-1.5 rounded-full text-sm font-medium transition-colors">
        🖊️ Dibuix
      </button>
    </div>
    <div v-if="loading" class="flex items-center justify-center h-48">
      <span class="text-gray-400 animate-pulse">Carregant tema…</span>
    </div>
    <div v-else class="relative">
      <div :class="mode === 'draw' ? 'pointer-events-none select-none' : ''">
        <AnnotationLayer :topic-id="topics.activeTopicId">
          <TopicContent :content="topicData?.content" :headings="topicData?.headings || []" />
        </AnnotationLayer>
      </div>
      <div v-if="mode === 'draw'" class="absolute top-0 left-0 w-full z-10">
        <DrawingCanvas :topic-id="topics.activeTopicId" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useTopicsStore } from '../stores/topics.js'
import { fetchTopicContent } from '../api/client.js'
import TopicContent from '../components/apunts/TopicContent.vue'
import AnnotationLayer from '../components/apunts/AnnotationLayer.vue'
import DrawingCanvas from '../components/apunts/DrawingCanvas.vue'

const topics = useTopicsStore()
const topicData = ref(null)
const loading = ref(false)
const mode = ref('text')

async function loadContent(id) {
  if (!id) return
  loading.value = true
  try {
    topicData.value = await fetchTopicContent(id)
  } finally {
    loading.value = false
  }
}

watch(() => topics.activeTopicId, loadContent, { immediate: true })
</script>
