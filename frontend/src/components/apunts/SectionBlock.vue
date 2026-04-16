<template>
  <div class="border border-[var(--color-border)] rounded-xl overflow-hidden bg-[var(--color-surface)] mb-2.5">
    <!-- Header -->
    <div class="flex items-center justify-between px-3.5 py-3 cursor-pointer select-none hover:bg-[#faf9ff] dark:hover:bg-gray-800/50"
         @click="open = !open">
      <div class="flex items-center gap-2 text-sm font-bold">
        <div class="w-[22px] h-[22px] rounded-[6px] flex items-center justify-center text-white text-[0.68rem] font-bold flex-shrink-0"
             :class="isRead ? 'bg-green-500' : 'bg-primary'">
          <template v-if="isRead">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          </template>
          <template v-else>{{ index + 1 }}</template>
        </div>
        <span :class="isRead ? 'text-gray-500 dark:text-gray-400' : ''">{{ title }}</span>
      </div>
      <div class="flex items-center gap-1.5">
        <button v-if="!enrichment && !loading" @click.stop="$emit('enrich', index)"
                class="text-[0.68rem] font-semibold px-2.5 py-1 rounded-full
                       border border-[#c4b5fd] bg-[#f5f3ff] text-primary
                       flex items-center gap-1 hover:bg-primary hover:text-white transition-colors">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
          </svg>
          Enriquir
        </button>
        <span v-else-if="loading"
              class="text-[0.68rem] font-semibold px-2.5 py-1 rounded-full
                     border border-[#c4b5fd] bg-[#f5f3ff] text-primary flex items-center gap-1">
          <svg class="animate-spin" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="9" stroke-opacity="0.25"/><path d="M12 3a9 9 0 0 1 9 9"/></svg>
          Generant…
        </span>
        <span v-else-if="enrichment"
              class="text-[0.68rem] font-semibold px-2.5 py-1 rounded-full
                     border border-green-300 bg-green-50 text-green-700 flex items-center gap-1">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          Enriquit
        </span>
        <span v-if="error" class="text-[0.65rem] text-red-500 flex items-center gap-1">
          <span class="max-w-[100px] truncate">{{ error }}</span>
          <a href="#" @click.prevent="$emit('enrich', index)" class="underline whitespace-nowrap">Tornar a intentar</a>
        </span>
        <svg class="w-3.5 h-3.5 text-[#c4b5fd] transition-transform"
             :class="open ? '' : 'rotate-180'"
             viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="18 15 12 9 6 15"/>
        </svg>
      </div>
    </div>

    <!-- Content -->
    <div v-if="open" class="px-3.5 pb-3.5 border-t border-[var(--color-border)]">
      <div v-if="enrichment"
           class="inline-flex items-center gap-1.5 text-[0.65rem] font-bold text-primary
                  bg-[#f5f3ff] border border-[#c4b5fd] px-2 py-0.5 rounded-full mt-2 mb-2">
        <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
        </svg>
        Generat per IA · {{ typeLabel(enrichment.type) }}
      </div>

      <TimelineView v-if="enrichment?.type === 'timeline'" :data="enrichment.data" />
      <ConceptCards v-else-if="enrichment?.type === 'cards'" :data="enrichment.data" />
      <ComparisonTable v-else-if="enrichment?.type === 'table'" :data="enrichment.data" />
      <CalloutBoxes v-else-if="enrichment?.type === 'callouts'" :data="enrichment.data" />

      <ProseContent :content="markdown" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ProseContent from './ProseContent.vue'
import TimelineView from './enriched/TimelineView.vue'
import ConceptCards from './enriched/ConceptCards.vue'
import ComparisonTable from './enriched/ComparisonTable.vue'
import CalloutBoxes from './enriched/CalloutBoxes.vue'

const props = defineProps({
  index: { type: Number, required: true },
  title: { type: String, required: true },
  markdown: { type: String, required: true },
  enrichment: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: null },
  isRead: { type: Boolean, default: false },
})

defineEmits(['enrich'])

const open = ref(true)

function typeLabel(type) {
  const map = { timeline: 'Timeline', cards: 'Cards', table: 'Taula comparativa', callouts: 'Callouts' }
  return map[type] || type
}
</script>
