<template>
  <div class="p-4 rounded-2xl border border-[var(--color-border)] space-y-4">
    <div v-if="loading" class="text-center py-6 text-gray-400 animate-pulse">
      L'IA analitza el teu progrés…
    </div>
    <template v-else-if="data">
      <div class="text-center">
        <p class="text-xs uppercase text-gray-400 mb-1">Preparació estimada</p>
        <p class="text-4xl font-bold"
           :class="data.readiness_pct >= 70 ? 'text-green-600' : data.readiness_pct >= 50 ? 'text-yellow-600' : 'text-red-500'">
          {{ data.readiness_pct }}%
        </p>
        <p class="text-lg font-semibold mt-1">Nota estimada: {{ data.nota_estimada }}/10</p>
        <p class="text-sm text-primary font-medium mt-1">
          📅 Examen el {{ data.exam_date }} — resten {{ data.dies_restants }} dies
        </p>
      </div>
      <div>
        <p class="text-xs font-semibold uppercase text-gray-400 mb-2">Temes prioritaris</p>
        <div class="space-y-1">
          <div v-for="(t, i) in data.temes_prioritaris" :key="i"
               class="flex items-center gap-2 text-sm">
            <span class="text-primary font-bold">{{ i + 1 }}.</span>
            <span>{{ t }}</span>
          </div>
        </div>
      </div>
      <div class="p-3 rounded-xl bg-blue-50 dark:bg-blue-900/20 text-sm">
        <p class="font-semibold text-blue-700 dark:text-blue-300 mb-1">Consell</p>
        <p class="text-gray-700 dark:text-gray-300">{{ data.consell_estudi }}</p>
      </div>
    </template>
    <div v-else class="text-center py-4">
      <button @click="load"
              class="px-5 py-2.5 bg-primary text-white rounded-xl text-sm font-medium">
        Analitzar amb IA
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { fetchExamReadiness } from '../../api/client.js'
const loading = ref(false)
const data = ref(null)
async function load() {
  loading.value = true
  try { data.value = await fetchExamReadiness() }
  finally { loading.value = false }
}
</script>
