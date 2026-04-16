<template>
  <div>
    <div class="overflow-x-auto flex gap-2 px-4 py-2 border-b border-[var(--color-border)]">
      <button v-for="t in topics.topics" :key="t.id"
              @click="selectTopic(t.id)"
              :class="activeTopic === t.id ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-gray-800'"
              class="flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap">
        T{{ t.number }}
      </button>
    </div>
    <div class="flex gap-2 px-4 py-2 border-b border-[var(--color-border)]">
      <button @click="generateCards"
              class="flex-1 py-2 bg-primary/10 text-primary rounded-xl text-sm font-medium hover:bg-primary/20">
        ✨ Generar amb IA
      </button>
      <button @click="showForm = !showForm"
              class="px-4 py-2 border border-[var(--color-border)] rounded-xl text-sm font-medium hover:border-primary">
        + Manual
      </button>
    </div>
    <div v-if="showForm" class="px-4 py-3 space-y-2 border-b border-[var(--color-border)] bg-[var(--color-surface)]">
      <input v-model="newCard.pregunta" placeholder="Terme / Pregunta"
             class="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] text-sm
                    bg-[var(--color-bg)] focus:outline-none focus:border-primary" />
      <input v-model="newCard.resposta" placeholder="Definició / Resposta"
             class="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] text-sm
                    bg-[var(--color-bg)] focus:outline-none focus:border-primary" />
      <input v-model="newCard.exemple" placeholder="Exemple (opcional)"
             class="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] text-sm
                    bg-[var(--color-bg)] focus:outline-none focus:border-primary" />
      <button @click="addCard" :disabled="!newCard.pregunta || !newCard.resposta"
              class="w-full py-2 bg-primary text-white rounded-xl text-sm font-semibold
                     disabled:opacity-50 disabled:cursor-not-allowed">
        Afegir targeta
      </button>
    </div>
    <div v-if="loading" class="flex justify-center py-12">
      <span class="animate-spin text-2xl">⏳</span>
    </div>
    <LeitnerDeck v-else :cards="cards" @generate="generateCards" @reviewed="reload" />
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { useTopicsStore } from '../stores/topics.js'
import { fetchFlashcards, generateFlashcards, createFlashcard } from '../api/client.js'
import LeitnerDeck from '../components/flashcards/LeitnerDeck.vue'

const topics = useTopicsStore()
const activeTopic = ref(topics.activeTopicId)
const cards = ref([])
const loading = ref(false)
const showForm = ref(false)
const newCard = reactive({ pregunta: '', resposta: '', exemple: '' })

async function loadCards(id) {
  loading.value = true
  try { cards.value = await fetchFlashcards(id) }
  finally { loading.value = false }
}

async function generateCards() {
  loading.value = true
  try { cards.value = await generateFlashcards(activeTopic.value) }
  finally { loading.value = false }
}

async function addCard() {
  await createFlashcard(activeTopic.value, { ...newCard })
  newCard.pregunta = ''; newCard.resposta = ''; newCard.exemple = ''
  showForm.value = false
  await reload()
}

async function reload() {
  cards.value = await fetchFlashcards(activeTopic.value)
}

function selectTopic(id) { activeTopic.value = id }
watch(activeTopic, loadCards, { immediate: true })
</script>
