<template>
  <div class="px-4 py-6 flex flex-col items-center gap-6">
    <div v-if="!dueCards.length" class="text-center py-12">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="text-primary mx-auto mb-3">
        <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2z"/>
      </svg>
      <p class="font-semibold text-lg">Cap targeta per avui!</p>
      <p class="text-gray-500 text-sm mt-1">Torna demà o genera noves targetes.</p>
      <button @click="$emit('generate')"
              class="mt-4 px-5 py-2 bg-primary text-white rounded-xl text-sm font-medium">
        Generar targetes amb IA
      </button>
    </div>
    <template v-else>
      <div class="w-full text-center text-sm text-gray-400 mb-1">
        {{ totalDue - dueCards.length }} / {{ totalDue }} revisades — Caixa {{ dueCards[0].leitner_box }}
      </div>
      <FlipCard :card="dueCards[0]" :key="dueCards[0].id" />
      <div class="flex gap-4 mt-4 w-full max-w-sm">
        <button @click="review(false)"
                class="flex-1 py-3 rounded-2xl bg-red-100 dark:bg-red-900/30
                       text-red-600 dark:text-red-400 font-semibold text-sm hover:bg-red-200
                       flex items-center justify-center gap-1.5">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          No sabia
        </button>
        <button @click="review(true)"
                class="flex-1 py-3 rounded-2xl bg-green-100 dark:bg-green-900/30
                       text-green-600 dark:text-green-400 font-semibold text-sm hover:bg-green-200
                       flex items-center justify-center gap-1.5">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          Sabia
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import FlipCard from './FlipCard.vue'
import { reviewFlashcard } from '../../api/client.js'

const props = defineProps({ cards: { type: Array, default: () => [] } })
const emit = defineEmits(['generate', 'reviewed'])

const today = new Date().toISOString().split('T')[0]

// Track reviewed card IDs locally so the card disappears immediately
// without waiting for the parent to reload props.cards.
const reviewedIds = ref(new Set())

// Reset when cards list changes (new topic or regenerated)
watch(() => props.cards, () => {
  reviewedIds.value = new Set()
}, { deep: false })

const allDue = computed(() =>
  props.cards.filter(c => c.next_review <= today)
)

const totalDue = computed(() => allDue.value.length)

const dueCards = computed(() =>
  allDue.value.filter(c => !reviewedIds.value.has(c.id))
)

async function review(knew) {
  const card = dueCards.value[0]
  if (!card) return
  // Mark as reviewed immediately — card disappears from dueCards right away
  reviewedIds.value = new Set([...reviewedIds.value, card.id])
  await reviewFlashcard(card.id, knew)
  emit('reviewed', card.id)
}
</script>
