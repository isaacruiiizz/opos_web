<template>
  <div>
    <!-- Mode switcher: two equal-width buttons filling the bar -->
    <div class="flex border-b border-[var(--color-border)]">
      <button @click="mode = 'text'"
              :class="mode === 'text' ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300'"
              class="flex-1 py-2 text-sm font-medium transition-colors flex items-center justify-center gap-1.5">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
        </svg>
        Text
      </button>
      <button @click="mode = 'draw'"
              :class="mode === 'draw' ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300'"
              class="flex-1 py-2 text-sm font-medium transition-colors flex items-center justify-center gap-1.5">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
        </svg>
        Dibuix
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-48">
      <span class="text-gray-400 animate-pulse">Carregant tema…</span>
    </div>

    <div v-else class="relative">
      <div :class="mode === 'draw' ? 'pointer-events-none select-none' : ''">
        <AnnotationLayer :topic-id="topics.activeTopicId">
          <div class="px-4 pb-20" ref="contentEl">
            <!-- Topic title -->
            <div class="mb-4 pt-3">
              <p class="text-[0.68rem] font-bold text-gray-400 tracking-widest uppercase mb-1">
                {{ topicData?.id?.replace('_', ' ') }}
              </p>
              <h1 class="text-xl font-extrabold leading-snug">{{ topicData?.title }}</h1>
            </div>

            <!-- AI Summary card -->
            <AISummaryCard
              :summary="summary"
              :loading="summaryLoading"
              :section-count="sections.length" />

            <!-- Section blocks -->
            <SectionBlock
              v-for="section in sections"
              :key="section.index"
              :index="section.index"
              :title="section.title"
              :markdown="section.markdown"
              :enrichment="enrichments[section.index] || null"
              :loading="enrichLoading[section.index] || false"
              :error="enrichErrors[section.index] || null"
              @enrich="handleEnrich" />
          </div>
        </AnnotationLayer>
      </div>

      <!-- Draw mode overlay -->
      <div v-if="mode === 'draw'" class="absolute top-0 left-0 w-full z-10">
        <DrawingCanvas :topic-id="topics.activeTopicId" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted, onUnmounted } from 'vue'
import { useTopicsStore } from '../stores/topics.js'
import { useUiStore } from '../stores/ui.js'
import {
  fetchTopicContent,
  fetchEnrichments,
  saveEnrichment,
  fetchTopicSummary,
  generateTopicSummary,
} from '../api/client.js'
import AnnotationLayer from '../components/apunts/AnnotationLayer.vue'
import DrawingCanvas from '../components/apunts/DrawingCanvas.vue'
import AISummaryCard from '../components/apunts/AISummaryCard.vue'
import SectionBlock from '../components/apunts/SectionBlock.vue'

// ── state ──────────────────────────────────────────────────────────────────
const topics = useTopicsStore()
const ui = useUiStore()
const topicData = ref(null)
const loading = ref(false)
const mode = ref('text')
const sections = ref([])
const enrichments = reactive({})
const enrichLoading = reactive({})
const enrichErrors = reactive({})
const summary = ref(null)
const summaryLoading = ref(false)

// ── section parser ─────────────────────────────────────────────────────────
function parseSections(markdown) {
  const lines = (markdown || '').split('\n')
  const result = []
  let current = null
  for (const line of lines) {
    if (line.startsWith('## ')) {
      if (current) result.push(current)
      current = { index: result.length, title: line.slice(3).trim(), markdown: '' }
    } else if (current) {
      current.markdown += line + '\n'
    }
  }
  if (current) result.push(current)
  if (result.length === 0 && markdown) {
    result.push({ index: 0, title: topicData.value?.title || 'Contingut', markdown })
  }
  return result
}

// ── load topic ─────────────────────────────────────────────────────────────
async function loadTopic(id) {
  if (!id) return
  loading.value = true
  summary.value = null
  summaryLoading.value = false
  sections.value = []
  Object.keys(enrichments).forEach(k => delete enrichments[k])
  Object.keys(enrichLoading).forEach(k => delete enrichLoading[k])
  Object.keys(enrichErrors).forEach(k => delete enrichErrors[k])
  ui.readingPct = 0

  try {
    topicData.value = await fetchTopicContent(id)
    sections.value = parseSections(topicData.value.content)
    const existing = await fetchEnrichments(id)
    existing.forEach(e => { enrichments[e.section_idx] = { type: e.type, data: e.data } })

    try {
      summary.value = await fetchTopicSummary(id)
    } catch {
      summaryLoading.value = true
      generateTopicSummary(id, topicData.value.content)
        .then(r => { summary.value = r })
        .catch(() => {})
        .finally(() => { summaryLoading.value = false })
    }
  } finally {
    loading.value = false
  }
}

// ── enrich a section ───────────────────────────────────────────────────────
async function handleEnrich(idx) {
  if (enrichLoading[idx]) return
  const section = sections.value.find(s => s.index === idx)
  if (!section) return

  enrichLoading[idx] = true
  delete enrichErrors[idx]
  try {
    const result = await saveEnrichment(topics.activeTopicId, idx, section.markdown)
    enrichments[idx] = { type: result.type, data: result.data }
  } catch (e) {
    enrichErrors[idx] = e.response?.data?.detail || 'Error generant'
  } finally {
    delete enrichLoading[idx]
  }
}

// ── scroll tracking → stored in ui store so Navbar can read it ─────────────
function onScroll() {
  const el = document.documentElement
  const scrollable = el.scrollHeight - el.clientHeight
  ui.readingPct = scrollable > 0 ? Math.round((el.scrollTop / scrollable) * 100) : 0
}

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
  ui.readingPct = 0
})

watch(() => topics.activeTopicId, (id) => {
  loadTopic(id)
}, { immediate: true })
</script>
