<template>
  <div>
    <div v-if="simulacre.phase === 'evaluating'" class="flex flex-col items-center justify-center min-h-[60vh] gap-4">
      <svg class="animate-spin h-10 w-10 text-amber-500" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
      </svg>
      <p class="text-sm text-[var(--color-text-muted)]">Avaluant respostes amb IA…</p>
      <p class="text-xs text-[var(--color-text-muted)]">Pot trigar fins a 30 segons</p>
    </div>
    <div v-else-if="simulacre.results">
      <SimulacreResults :results="simulacre.results" @new-exam="startNew" @re-evaluate="simulacre.reEvaluate()" />
    </div>
    <div v-else class="text-center py-12 text-[var(--color-text-muted)] text-sm">
      No hi ha cap resultat.
      <router-link to="/practica" class="text-primary underline ml-1">Torna a Pràctica</router-link>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSimulacreStore } from '../stores/simulacre.js'
import SimulacreResults from '../components/practice/SimulacreResults.vue'

const router = useRouter()
const simulacre = useSimulacreStore()

onMounted(() => {
  if (simulacre.results && simulacre.phase !== 'results') {
    simulacre.phase = 'results'
  }
})

function startNew() {
  simulacre.reset()
  router.push('/practica')
}
</script>
