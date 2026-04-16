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
    <div v-if="loading" class="flex flex-col items-center justify-center py-16 gap-4">
      <span class="text-4xl animate-spin">⏳</span>
      <p class="text-sm text-gray-500">Generant amb IA, pot trigar uns segons…</p>
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

async function startMode(mode) {
  activeMode.value = mode
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

watch(activeTopic, () => {
  activeMode.value = null
  questions.value = []
})
</script>
