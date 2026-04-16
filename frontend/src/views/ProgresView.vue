<template>
  <div class="px-4 py-6 space-y-6 pb-24">
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
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onActivated } from 'vue'
import { fetchProgress } from '../api/client.js'
import ProgressBar from '../components/progres/ProgressBar.vue'
import ExamReadiness from '../components/progres/ExamReadiness.vue'

const progress = ref(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try { progress.value = await fetchProgress() }
  finally { loading.value = false }
}

onMounted(load)
onActivated(load)
</script>
