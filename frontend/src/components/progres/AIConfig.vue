<template>
  <div class="space-y-4">
    <p class="font-semibold text-sm uppercase text-gray-400">Configuració IA</p>

    <!-- Model selector -->
    <div class="p-4 rounded-2xl border border-[var(--color-border)] space-y-3">
      <div class="flex items-center justify-between">
        <span class="text-sm font-semibold">Model actiu</span>
        <button @click="loadData" :disabled="loading"
                class="text-xs text-gray-400 hover:text-primary disabled:opacity-40 flex items-center gap-1">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.95"/>
          </svg>
          Actualitzar
        </button>
      </div>

      <div v-if="loading" class="text-xs text-gray-400 animate-pulse">Carregant…</div>

      <template v-else>
        <select v-model="selectedModel" @change="changeModel"
                class="w-full rounded-xl border border-[var(--color-border)] px-3 py-2 text-sm
                       bg-[var(--color-surface)] focus:outline-none focus:border-primary">
          <option v-for="m in models" :key="m.id" :value="m.id" :disabled="m.supported === false">
            {{ m.supported === false ? '[×] ' : '' }}{{ m.display_name || m.id }}
            {{ m.description ? `— ${m.description}` : '' }}
          </option>
        </select>

        <p v-if="currentModelInfo?.supported === false"
           class="text-xs text-orange-500 flex items-center gap-1">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          Aquest model no suporta generació de text. Selecciona un altre model.
        </p>

        <!-- Limits del model seleccionat -->
        <div v-if="currentModelInfo" class="grid grid-cols-3 gap-2 text-xs text-center">
          <div class="rounded-lg bg-gray-100 dark:bg-gray-800 p-2">
            <p class="font-bold text-primary">{{ currentModelInfo.rpm ?? '?' }}</p>
            <p class="text-gray-400">req/min</p>
          </div>
          <div class="rounded-lg bg-gray-100 dark:bg-gray-800 p-2">
            <p class="font-bold text-primary">
              {{ currentModelInfo.tpm ? (currentModelInfo.tpm / 1000) + 'k' : '∞' }}
            </p>
            <p class="text-gray-400">tok/min</p>
          </div>
          <div class="rounded-lg bg-gray-100 dark:bg-gray-800 p-2">
            <p class="font-bold text-primary">
              {{ currentModelInfo.rpd ? currentModelInfo.rpd.toLocaleString() : '?' }}
            </p>
            <p class="text-gray-400">req/dia</p>
          </div>
        </div>
      </template>
    </div>

    <!-- Usage stats -->
    <div v-if="status && !loading" class="p-4 rounded-2xl border border-[var(--color-border)] space-y-3">
      <div class="flex items-center justify-between">
        <span class="text-sm font-semibold">Ús actual</span>
        <span class="text-xs text-gray-400">
          min: {{ status.usage.minute_elapsed_s }}s / 60s
        </span>
      </div>

      <!-- Peticions per minut -->
      <div v-if="status.limits.rpm" class="space-y-1">
        <div class="flex justify-between text-xs">
          <span class="text-gray-500">Peticions (min)</span>
          <span class="font-medium">{{ status.usage.req_minute }}/{{ status.limits.rpm }}</span>
        </div>
        <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div class="h-full rounded-full transition-all"
               :class="usageColor(status.usage.req_minute, status.limits.rpm)"
               :style="{ width: pct(status.usage.req_minute, status.limits.rpm) + '%' }" />
        </div>
      </div>

      <!-- Tokens per minut -->
      <div v-if="status.limits.tpm" class="space-y-1">
        <div class="flex justify-between text-xs">
          <span class="text-gray-500">Tokens (min)</span>
          <span class="font-medium">
            {{ status.usage.tok_minute.toLocaleString() }}/{{ (status.limits.tpm / 1000) + 'k' }}
          </span>
        </div>
        <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div class="h-full rounded-full transition-all"
               :class="usageColor(status.usage.tok_minute, status.limits.tpm)"
               :style="{ width: pct(status.usage.tok_minute, status.limits.tpm) + '%' }" />
        </div>
      </div>
      <div v-else class="text-xs text-gray-400">Tokens per minut: il·limitats ∞</div>

      <!-- Peticions per dia -->
      <div v-if="status.limits.rpd" class="space-y-1">
        <div class="flex justify-between text-xs">
          <span class="text-gray-500">Peticions (dia)</span>
          <span class="font-medium">{{ status.usage.req_day }}/{{ status.limits.rpd.toLocaleString() }}</span>
        </div>
        <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div class="h-full rounded-full transition-all"
               :class="usageColor(status.usage.req_day, status.limits.rpd)"
               :style="{ width: pct(status.usage.req_day, status.limits.rpd) + '%' }" />
        </div>
      </div>
    </div>

    <!-- Saved confirmation -->
    <p v-if="saved" class="text-xs text-green-600 text-center animate-pulse flex items-center justify-center gap-1">
      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
      Model desat correctament
    </p>
    <p v-if="saveError" class="text-xs text-red-500 text-center flex items-center justify-center gap-1">
      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      Error desant el model
    </p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchAIModels, fetchAIStatus, setAIModel } from '../../api/client.js'

const models = ref([])
const status = ref(null)
const loading = ref(false)
const selectedModel = ref('')
const saved = ref(false)
const saveError = ref(false)

const currentModelInfo = computed(() =>
  models.value.find(m => m.id === selectedModel.value) || null
)

async function loadData() {
  loading.value = true
  try {
    const [m, s] = await Promise.all([fetchAIModels(), fetchAIStatus()])
    models.value = m
    status.value = s
    selectedModel.value = s.model
  } finally {
    loading.value = false
  }
}

async function changeModel() {
  saved.value = false
  saveError.value = false
  if (currentModelInfo.value?.supported === false) return
  try {
    await setAIModel(selectedModel.value)
    status.value = await fetchAIStatus()
    saved.value = true
    setTimeout(() => { saved.value = false }, 3000)
  } catch {
    saveError.value = true
  }
}

function pct(used, limit) {
  return Math.min(100, Math.round(used / limit * 100))
}

function usageColor(used, limit) {
  const p = pct(used, limit)
  if (p >= 90) return 'bg-red-500'
  if (p >= 70) return 'bg-orange-400'
  return 'bg-primary'
}

onMounted(loadData)
</script>
