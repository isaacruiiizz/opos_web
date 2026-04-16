<template>
  <div class="px-4 py-6 space-y-6 pb-24">

    <!-- Model d'IA -->
    <section>
      <p class="text-xs font-bold uppercase tracking-widest text-gray-400 mb-3">Model d'IA</p>
      <AIConfig />
    </section>

    <!-- Anàlisi del temari -->
    <section>
      <p class="text-xs font-bold uppercase tracking-widest text-gray-400 mb-3">Temari oficial</p>
      <div class="p-4 rounded-2xl border border-[var(--color-border)] space-y-3">
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Analitza la cobertura dels apunts respecte al temari oficial en PDF.
        </p>

        <!-- PDF absent -->
        <div v-if="pdfExists === false"
             class="flex items-start gap-2 p-3 rounded-xl bg-orange-50 dark:bg-orange-900/20
                    border border-orange-200 dark:border-orange-800 text-xs text-orange-700 dark:text-orange-400">
          <svg class="flex-shrink-0 mt-0.5" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          <span>El fitxer PDF no existeix al servidor. Puja-lo a <code class="font-mono bg-orange-100 dark:bg-orange-900/40 px-1 rounded">/data/</code> i reinicia el backend.</span>
        </div>

        <button @click="runPdf" :disabled="pdfLoading || pdfExists === false"
                class="w-full py-2.5 border border-[var(--color-border)] rounded-xl text-sm
                       font-medium text-gray-600 dark:text-gray-400 hover:border-primary
                       hover:text-primary disabled:opacity-50 flex items-center justify-center gap-2">
          <svg v-if="pdfLoading" class="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <circle cx="12" cy="12" r="9" stroke-opacity="0.25"/><path d="M12 3a9 9 0 0 1 9 9"/>
          </svg>
          <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          {{ pdfLoading ? 'Analitzant… (pot trigar uns minuts)' : 'Analitzar cobertura del temari' }}
        </button>
        <p v-if="pdfDone" class="text-xs text-green-600 flex items-center gap-1">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          Anàlisi completada. Vés a Progrés per veure els resultats.
        </p>
        <p v-if="pdfError" class="text-xs text-red-500 flex items-start gap-1">
          <svg class="flex-shrink-0 mt-0.5" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          {{ pdfError }}
        </p>
      </div>
    </section>

    <!-- Gestió de dades -->
    <section>
      <p class="text-xs font-bold uppercase tracking-widest text-gray-400 mb-3">Gestió de dades</p>
      <div class="rounded-2xl border border-[var(--color-border)] divide-y divide-[var(--color-border)] overflow-hidden">

        <!-- Enriquiments IA -->
        <div class="p-4 flex items-center justify-between gap-3">
          <div class="min-w-0">
            <p class="text-sm font-medium">Enriquiments IA</p>
            <p class="text-xs text-gray-400 mt-0.5">Cards, timelines, taules i resums generats per IA</p>
          </div>
          <button @click="confirmClear('enrichments')" :disabled="busy.enrichments"
                  class="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-xl
                         border border-red-200 dark:border-red-800 text-xs font-medium
                         text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20
                         disabled:opacity-40 transition-colors">
            <svg v-if="busy.enrichments" class="animate-spin" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="9" stroke-opacity="0.25"/><path d="M12 3a9 9 0 0 1 9 9"/></svg>
            <svg v-else width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
            Esborrar
          </button>
        </div>

        <!-- Targetes flash -->
        <div class="p-4 flex items-center justify-between gap-3">
          <div class="min-w-0">
            <p class="text-sm font-medium">Targetes flash</p>
            <p class="text-xs text-gray-400 mt-0.5">Totes les targetes i el seu progrés Leitner</p>
          </div>
          <button @click="confirmClear('flashcards')" :disabled="busy.flashcards"
                  class="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-xl
                         border border-red-200 dark:border-red-800 text-xs font-medium
                         text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20
                         disabled:opacity-40 transition-colors">
            <svg v-if="busy.flashcards" class="animate-spin" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="9" stroke-opacity="0.25"/><path d="M12 3a9 9 0 0 1 9 9"/></svg>
            <svg v-else width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
            Esborrar
          </button>
        </div>

        <!-- Dibuixos -->
        <div class="p-4 flex items-center justify-between gap-3">
          <div class="min-w-0">
            <p class="text-sm font-medium">Dibuixos</p>
            <p class="text-xs text-gray-400 mt-0.5">Tots els dibuixos fets sobre els apunts</p>
          </div>
          <button @click="confirmClear('drawings')" :disabled="busy.drawings"
                  class="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-xl
                         border border-red-200 dark:border-red-800 text-xs font-medium
                         text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20
                         disabled:opacity-40 transition-colors">
            <svg v-if="busy.drawings" class="animate-spin" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="9" stroke-opacity="0.25"/><path d="M12 3a9 9 0 0 1 9 9"/></svg>
            <svg v-else width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
            Esborrar
          </button>
        </div>

        <!-- Progrés -->
        <div class="p-4 flex items-center justify-between gap-3">
          <div class="min-w-0">
            <p class="text-sm font-medium">Progrés i sessions</p>
            <p class="text-xs text-gray-400 mt-0.5">Totes les puntuacions i l'historial de pràctica</p>
          </div>
          <button @click="confirmClear('progress')" :disabled="busy.progress"
                  class="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-xl
                         border border-red-200 dark:border-red-800 text-xs font-medium
                         text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20
                         disabled:opacity-40 transition-colors">
            <svg v-if="busy.progress" class="animate-spin" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="9" stroke-opacity="0.25"/><path d="M12 3a9 9 0 0 1 9 9"/></svg>
            <svg v-else width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
            Reiniciar
          </button>
        </div>

      </div>

      <!-- Feedback messages -->
      <div class="mt-2 space-y-1">
        <p v-for="(msg, key) in feedback" :key="key"
           :class="msg.ok ? 'text-green-600' : 'text-red-500'"
           class="text-xs flex items-center gap-1">
          <svg v-if="msg.ok" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          <svg v-else width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          {{ msg.text }}
        </p>
      </div>
    </section>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import AIConfig from '../components/progres/AIConfig.vue'
import { fetchPdfStatus, runPdfAnalysis, resetProgress, clearEnrichments, clearFlashcards, clearDrawings } from '../api/client.js'

const pdfLoading = ref(false)
const pdfDone = ref(false)
const pdfError = ref(null)
const pdfExists = ref(null)   // null = checking, true/false = result
const busy = reactive({ enrichments: false, flashcards: false, drawings: false, progress: false })
const feedback = reactive({})

onMounted(async () => {
  try {
    const status = await fetchPdfStatus()
    pdfExists.value = status.exists
  } catch {
    pdfExists.value = null
  }
})

async function runPdf() {
  pdfLoading.value = true
  pdfDone.value = false
  pdfError.value = null
  try {
    await runPdfAnalysis()
    pdfDone.value = true
  } catch (e) {
    pdfError.value = e.response?.data?.detail || 'Error en l\'anàlisi del PDF.'
  } finally {
    pdfLoading.value = false
  }
}

const LABELS = {
  enrichments: 'enriquiments i resums IA',
  flashcards:  'targetes flash',
  drawings:    'dibuixos',
  progress:    'progrés i sessions',
}

const ACTIONS = {
  enrichments: clearEnrichments,
  flashcards:  clearFlashcards,
  drawings:    clearDrawings,
  progress:    resetProgress,
}

async function confirmClear(key) {
  const label = LABELS[key]
  if (!confirm(`Segur que vols esborrar tots els ${label}? Aquesta acció no es pot desfer.`)) return
  busy[key] = true
  delete feedback[key]
  try {
    await ACTIONS[key]()
    feedback[key] = { ok: true, text: `${label.charAt(0).toUpperCase() + label.slice(1)} esborrats correctament.` }
    setTimeout(() => { delete feedback[key] }, 4000)
  } catch {
    feedback[key] = { ok: false, text: `Error esborrant els ${label}.` }
  } finally {
    busy[key] = false
  }
}
</script>
