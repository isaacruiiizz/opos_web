<template>
  <div class="w-full max-w-sm mx-auto h-52 cursor-pointer" @click="flipped = !flipped">
    <!-- Front -->
    <div v-if="!flipped" class="h-full rounded-2xl flex flex-col items-center justify-center
                p-6 bg-white dark:bg-gray-800 shadow-xl border border-gray-100 dark:border-gray-700">
      <p class="text-xs font-semibold uppercase text-gray-400 mb-2">Concepte</p>
      <p class="text-center font-medium text-lg">{{ card.pregunta }}</p>
    </div>
    <!-- Back -->
    <div v-else class="h-full rounded-2xl flex flex-col items-center justify-center
                p-6 bg-primary/5 dark:bg-primary/10 shadow-xl border border-primary/20">
      <p class="text-xs font-semibold uppercase text-primary/70 mb-2">Definició</p>
      <p class="text-center font-medium">{{ card.resposta }}</p>
      <p v-if="card.exemple" class="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center italic">
        {{ card.exemple }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
const props = defineProps({ card: Object })
const flipped = ref(false)
watch(() => props.card, () => { flipped.value = false })
</script>
