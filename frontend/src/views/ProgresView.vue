<template>
  <div class="px-4 py-6 space-y-6 pb-20">
    <div v-if="loading" class="text-center py-12 text-gray-400 animate-pulse">Carregant progrés…</div>
    <template v-else-if="progress">
      <div class="text-center">
        <p class="text-xs uppercase text-gray-400 mb-1">Progrés global</p>
        <p class="text-5xl font-bold text-primary">{{ progress.overall_pct }}%</p>
      </div>
      <div class="space-y-3">
        <ProgressBar label="Bloc General" :pct="progress.general_pct" />
        <ProgressBar label="Bloc Específic" :pct="progress.especific_pct" />
      </div>
      <div>
        <p class="font-semibold text-sm uppercase text-gray-400 mb-3">Per tema</p>
        <div class="space-y-2">
          <ProgressBar v-for="t in progress.topics" :key="t.topic_id"
                       :label="`T${t.topic_id.split('_')[1]} ${t.title || ''}`"
                       :pct="t.overall_pct" />
        </div>
      </div>
      <ExamReadiness />
      <div v-if="progress.history.length">
        <p class="font-semibold text-sm uppercase text-gray-400 mb-3">Últimes sessions</p>
        <div class="space-y-2">
          <div v-for="(h, i) in progress.history" :key="i"
               class="flex items-center justify-between text-sm p-3
                      rounded-xl border border-[var(--color-border)]">
            <span class="truncate text-gray-600 dark:text-gray-400">
              {{ h.topic_id }} · {{ h.mode }}
            </span>
            <span class="font-bold text-primary ml-2">{{ h.score }}/10</span>
          </div>
        </div>
      </div>
      <button @click="runPdf" :disabled="pdfLoading"
              class="w-full py-3 border border-[var(--color-border)] rounded-2xl text-sm
                     font-medium text-gray-600 dark:text-gray-400 hover:border-primary
                     hover:text-primary disabled:opacity-50 flex items-center justify-center gap-2">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        {{ pdfLoading ? 'Analitzant temari…' : 'Analitzar cobertura del temari oficial' }}
      </button>
      <AIConfig />
      <button @click="confirmReset"
              class="w-full py-3 border border-red-200 dark:border-red-800 rounded-2xl text-sm
                     font-medium text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20
                     flex items-center justify-center gap-2">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
        </svg>
        Reiniciar tot el progrés
      </button>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onActivated } from 'vue'
import { fetchProgress, runPdfAnalysis, resetProgress } from '../api/client.js'
import ProgressBar from '../components/progres/ProgressBar.vue'
import ExamReadiness from '../components/progres/ExamReadiness.vue'
import AIConfig from '../components/progres/AIConfig.vue'

const progress = ref(null)
const loading = ref(false)
const pdfLoading = ref(false)

async function load() {
  loading.value = true
  try { progress.value = await fetchProgress() }
  finally { loading.value = false }
}

async function runPdf() {
  pdfLoading.value = true
  try { await runPdfAnalysis() }
  finally { pdfLoading.value = false }
}

async function confirmReset() {
  if (!confirm('Segur que vols reiniciar tot el progrés? Això esborrarà totes les puntuacions i sessions.')) return
  await resetProgress()
  await load()
}

onMounted(load)
onActivated(load)
</script>
