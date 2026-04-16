<template>
  <div>
    <div class="overflow-x-auto flex gap-2 px-4 py-2 border-b border-[var(--color-border)]">
      <button v-for="t in topics.topics" :key="t.id"
              @click="activeTopic = t.id"
              :class="activeTopic === t.id ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-gray-800'"
              class="flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap">
        T{{ t.number }}
      </button>
    </div>
    <div v-if="loading" class="flex flex-col items-center justify-center px-8 py-16 gap-6">
      <p class="text-base font-medium">Generant {{ modeLabel }} amb IA…</p>
      <div class="w-full max-w-sm h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div class="h-full bg-primary rounded-full animate-progress" />
      </div>
      <p class="text-xs text-gray-400">Pot trigar entre 10 i 20 segons. No surtis de la pantalla.</p>
    </div>
    <div v-else-if="errorMsg" class="mx-4 mt-6 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
      <p class="font-medium mb-1">No s'ha pogut generar</p>
      <p>{{ errorMsg }}</p>
      <button @click="errorMsg = null" class="mt-3 text-xs underline">Torna al selector</button>
    </div>
    <ModeSelector v-else-if="!activeMode" @select="startMode" />
    <TestMode v-else-if="activeMode === 'test' && questions.length"
              :questions="questions" :topic-id="activeTopic"
              @done="finishSession" />
    <BreusMode v-else-if="activeMode === 'breus' && questions.length"
               :questions="questions" :topic-id="activeTopic"
               @done="finishSession" />
    <SupositMode v-else-if="activeMode === 'suposit' && suposit"
                 :suposit="suposit" :topic-id="activeTopic"
                 @done="finishSession" />
    <ConnectaMode v-else-if="activeMode === 'connecta' && questions.length"
                  :pairs="questions" :topic-id="activeTopic"
                  @done="finishSession" />
    <BuitsMode v-else-if="activeMode === 'buits' && questions.length"
               :sentences="questions" :topic-id="activeTopic"
               @done="finishSession" />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useTopicsStore } from '../stores/topics.js'
import { generatePractice, saveSession } from '../api/client.js'
import ModeSelector from '../components/practice/ModeSelector.vue'
import TestMode from '../components/practice/TestMode.vue'
import BreusMode from '../components/practice/BreusMode.vue'
import SupositMode from '../components/practice/SupositMode.vue'
import ConnectaMode from '../components/practice/ConnectaMode.vue'
import BuitsMode from '../components/practice/BuitsMode.vue'

const topics = useTopicsStore()
const activeTopic = ref(topics.activeTopicId)
const activeMode = ref(null)
const questions = ref([])
const suposit = ref(null)
const loading = ref(false)
const errorMsg = ref(null)
const modeLabels = { test: 'el test', breus: 'les preguntes breus', suposit: 'el supòsit', connecta: 'el connecta', buits: 'els espais en blanc' }
const modeLabel = ref('')

// Cache per tema: no fem nova petició si ja tenim les preguntes generades
const sessionCache = new Map()

async function startMode(mode) {
  activeMode.value = mode
  modeLabel.value = modeLabels[mode] || mode
  loading.value = true
  errorMsg.value = null
  try {
    const data = await generatePractice(activeTopic.value, mode)
    if (mode === 'suposit') { suposit.value = data }
    else { questions.value = data }
  } catch (e) {
    const detail = e.response?.data?.detail
    errorMsg.value = detail || 'Error generant la pràctica. Torna a intentar-ho.'
    activeMode.value = null
  } finally {
    loading.value = false
  }
}

async function finishSession(score) {
  sessionCache.delete(activeTopic.value)
  await saveSession({
    topic_id: activeTopic.value,
    mode: activeMode.value,
    score,
    questions_json: JSON.stringify(questions.value),
    answers_json: '[]',
    feedback_json: '{}',
  })
  topics.updateTopicProgress(activeTopic.value, score * 10)
  activeMode.value = null
  questions.value = []
  suposit.value = null
}

watch(activeTopic, (newId, oldId) => {
  // Desa l'estat del tema anterior
  if (oldId) {
    sessionCache.set(oldId, {
      activeMode: activeMode.value,
      questions: questions.value,
      suposit: suposit.value,
    })
  }
  // Restaura l'estat del tema nou si existeix a la caché
  const cached = sessionCache.get(newId)
  if (cached?.activeMode) {
    activeMode.value = cached.activeMode
    questions.value = cached.questions
    suposit.value = cached.suposit
  } else {
    activeMode.value = null
    questions.value = []
    suposit.value = null
  }
})
</script>

<style scoped>
@keyframes progress {
  0%   { width: 0% }
  60%  { width: 80% }
  90%  { width: 92% }
  100% { width: 95% }
}
.animate-progress {
  animation: progress 18s ease-out forwards;
}
</style>
