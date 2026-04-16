<template>
  <div class="px-4 py-6 flex flex-col items-center gap-6">
    <div v-if="!dueCards.length" class="text-center py-12">
      <p class="text-4xl mb-3">🎉</p>
      <p class="font-semibold text-lg">Cap targeta per avui!</p>
      <p class="text-gray-500 text-sm mt-1">Torna demà o genera noves targetes.</p>
      <button @click="$emit('generate')"
              class="mt-4 px-5 py-2 bg-primary text-white rounded-xl text-sm font-medium">
        Generar targetes amb IA
      </button>
    </div>
    <template v-else>
      <div class="w-full text-center text-sm text-gray-400 mb-1">
        {{ current + 1 }} / {{ dueCards.length }} — Caixa {{ dueCards[current].leitner_box }}
      </div>
      <FlipCard :card="dueCards[current]" />
      <div class="flex gap-4 mt-4 w-full max-w-sm">
        <button @click="review(false)"
                class="flex-1 py-3 rounded-2xl bg-red-100 dark:bg-red-900/30
                       text-red-600 dark:text-red-400 font-semibold text-sm hover:bg-red-200">
          ✗ No sabia
        </button>
        <button @click="review(true)"
                class="flex-1 py-3 rounded-2xl bg-green-100 dark:bg-green-900/30
                       text-green-600 dark:text-green-400 font-semibold text-sm hover:bg-green-200">
          ✓ Sabia
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import FlipCard from './FlipCard.vue'
import { reviewFlashcard } from '../../api/client.js'

const props = defineProps({ cards: { type: Array, default: () => [] } })
const emit = defineEmits(['generate', 'reviewed'])

const today = new Date().toISOString().split('T')[0]
const dueCards = computed(() =>
  props.cards.filter(c => c.next_review <= today)
)
const current = ref(0)

async function review(knew) {
  const card = dueCards.value[current.value]
  await reviewFlashcard(card.id, knew)
  emit('reviewed', card.id)
  if (current.value < dueCards.value.length - 1) {
    current.value++
  }
}
</script>
