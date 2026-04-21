<template>
  <div class="mx-4 mt-4 mb-2 rounded-xl border-2 border-amber-400 bg-amber-50 dark:bg-amber-950/30 dark:border-amber-500 p-4">
    <div class="flex items-start justify-between gap-3">
      <div>
        <div class="flex items-center gap-2 mb-1">
          <span class="text-lg">🎯</span>
          <h2 class="font-bold text-amber-900 dark:text-amber-300 text-sm">Simulacre d'Examen Oficial</h2>
        </div>
        <p class="text-xs text-amber-700 dark:text-amber-400">15 preguntes · 2 hores · Nota /10 · Mínim 5 per aprovar</p>
        <p v-if="roundState" class="text-xs text-amber-600 dark:text-amber-500 mt-0.5">
          Ronda {{ roundState.round }} · {{ roundState.covered }}/{{ roundState.total }} temes coberts
        </p>
        <p v-else class="text-xs text-amber-600 dark:text-amber-500 mt-0.5">Temes "a tenir en compte"</p>
      </div>

      <div v-if="lastResult" class="text-right shrink-0">
        <div class="text-sm font-bold" :class="lastResult.passed ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'">
          {{ lastResult.score?.toFixed(1) }}/10
        </div>
        <div class="text-xs" :class="lastResult.passed ? 'text-green-600' : 'text-red-500'">
          {{ lastResult.passed ? '✓ Aprovat' : '✗ Suspès' }}
        </div>
      </div>
    </div>

    <div v-if="error" class="mt-3 p-2 bg-red-100 dark:bg-red-900/40 rounded-lg text-xs text-red-700 dark:text-red-300">
      ⚠️ {{ error }}
    </div>

    <div v-if="hasDraft && !error" class="mt-3 p-2 bg-amber-100 dark:bg-amber-900/40 rounded-lg text-xs text-amber-800 dark:text-amber-300">
      ⚠️ Tens un examen en curs desat. En iniciar, el reprendràs.
    </div>

    <button
      @click="$emit('start')"
      :disabled="generating"
      class="mt-3 w-full py-2.5 rounded-lg font-semibold text-sm transition-all"
      :class="generating
        ? 'bg-amber-200 dark:bg-amber-900 text-amber-500 cursor-not-allowed'
        : 'bg-amber-500 hover:bg-amber-600 text-white active:scale-95'"
    >
      <span v-if="generating" class="flex items-center justify-center gap-2">
        <svg class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        Generant preguntes…
      </span>
      <span v-else>{{ hasDraft ? 'Reprendre Simulacre' : 'Iniciar Simulacre' }}</span>
    </button>
  </div>
</template>

<script setup>
defineProps({
  lastResult: { type: Object, default: null },
  generating: { type: Boolean, default: false },
  hasDraft: { type: Boolean, default: false },
  error: { type: String, default: null },
  roundState: { type: Object, default: null },
})
defineEmits(['start'])
</script>
