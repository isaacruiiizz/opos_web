<template>
  <div class="px-4 py-6 max-w-lg mx-auto">
    <div v-if="evalResult" class="space-y-4">
      <div class="p-4 rounded-2xl border border-[var(--color-border)]">
        <p class="text-xs text-gray-400 mb-1">Puntuació</p>
        <p class="text-3xl font-bold"
           :class="evalResult.puntuacio >= 7 ? 'text-green-600' : 'text-yellow-600'">
          {{ evalResult.puntuacio }}/10
        </p>
      </div>
      <div class="p-4 rounded-2xl bg-green-50 dark:bg-green-900/20 text-sm">
        <p class="font-semibold mb-1 text-green-700 dark:text-green-400">Encerts</p>
        <ul class="list-disc list-inside space-y-1">
          <li v-for="(e, i) in evalResult.encerts" :key="i">{{ e }}</li>
        </ul>
      </div>
      <div v-if="evalResult.mancances.length" class="p-4 rounded-2xl bg-red-50 dark:bg-red-900/20 text-sm">
        <p class="font-semibold mb-1 text-red-700 dark:text-red-400">Mancances</p>
        <ul class="list-disc list-inside space-y-1">
          <li v-for="(m, i) in evalResult.mancances" :key="i">{{ m }}</li>
        </ul>
      </div>
      <p class="text-sm text-gray-600 dark:text-gray-300">{{ evalResult.feedback }}</p>
      <button @click="$emit('done', evalResult.puntuacio)"
              class="w-full py-3 bg-primary text-white rounded-2xl font-semibold">
        Tornar als modes
      </button>
    </div>
    <div v-else>
      <div v-if="loading" class="text-center py-12 text-gray-400 animate-pulse">L'IA avalua…</div>
      <template v-else>
        <button @click="emit('cancel', { inProgress: true })"
                class="mb-3 flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
          ← Sortir
        </button>
        <div class="p-4 rounded-2xl bg-blue-50 dark:bg-blue-900/20 mb-4">
          <p class="text-xs font-semibold text-blue-600 dark:text-blue-400 mb-2">Supòsit pràctic</p>
          <p class="text-sm font-medium">{{ suposit.enunciat }}</p>
          <p v-if="suposit.context" class="text-xs text-gray-500 mt-2 italic">
            Context: {{ suposit.context }}
          </p>
          <p class="text-xs text-gray-400 mt-2">Dificultat: {{ suposit.dificultat }}</p>
        </div>
        <p class="text-xs text-gray-400 mb-2">Escriu la teva resposta raonada:</p>
        <textarea v-model="resposta" rows="8"
                  placeholder="Desenvolupa la teva resposta..."
                  class="w-full rounded-2xl border border-[var(--color-border)] p-3 text-sm
                         bg-[var(--color-surface)] resize-none focus:outline-none focus:border-primary" />
        <button @click="submit" :disabled="!resposta.trim()"
                class="w-full mt-4 py-3 bg-primary text-white rounded-2xl font-semibold
                       disabled:opacity-50 disabled:cursor-not-allowed">
          Avaluar amb IA
        </button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { evaluateAnswer } from '../../api/client.js'

const props = defineProps({ suposit: Object, topicId: String })
const emit = defineEmits(['done', 'cancel'])

const resposta = ref('')
const evalResult = ref(null)
const loading = ref(false)

async function submit() {
  loading.value = true
  try {
    evalResult.value = await evaluateAnswer({
      topic_id: props.topicId,
      mode: 'suposit',
      pregunta: props.suposit.enunciat,
      resposta_usuari: resposta.value,
      resposta_model: (props.suposit.punts_clau_resposta || []).join('; '),
    })
  } finally { loading.value = false }
}
</script>
