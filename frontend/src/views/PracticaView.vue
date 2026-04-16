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
    <div v-if="loading" class="flex justify-center py-12">
      <span class="animate-spin text-3xl">⏳</span>
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

async function startMode(mode) {
  activeMode.value = mode
  loading.value = true
  try {
    const data = await generatePractice(activeTopic.value, mode)
    if (mode === 'suposit') { suposit.value = data }
    else { questions.value = data }
  } finally { loading.value = false }
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
