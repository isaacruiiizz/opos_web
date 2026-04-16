<template>
  <div class="grid grid-cols-2 gap-2 mt-1">
    <div v-for="(card, i) in data" :key="i"
         class="bg-[#f5f3ff] border border-[#e0d9f7] rounded-xl p-3 text-center">
      <div class="w-8 h-8 bg-white rounded-lg mx-auto mb-2 flex items-center justify-center shadow-sm">
        <component :is="iconComponent(card.icon)" class="w-4 h-4 text-primary" />
      </div>
      <p class="text-xs font-bold text-primary mb-1">{{ card.title }}</p>
      <p class="text-[0.68rem] text-gray-500 leading-snug">{{ card.desc }}</p>
    </div>
  </div>
</template>

<script setup>
import { h } from 'vue'

defineProps({ data: { type: Array, required: true } })

const ICONS = {
  building: 'M3 9h18v13H3zM8 22V12h8v10M3 9V7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v2M12 5V2',
  user: 'M12 8m-4 0a4 4 0 1 0 8 0a4 4 0 1 0-8 0M4 20c0-4 3.6-7 8-7s8 3 8 7',
  file: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H9H8',
  scale: 'm16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1zM2 16l3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1zM7 21h10M12 3v18M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2',
  shield: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z',
  clock: 'M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2zM12 6v6l4 2',
  globe: 'M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2zM2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z',
  users: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75',
  key: 'M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0 3 3L22 7l-3-3m-3.5 3.5L19 4',
  flag: 'M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1zM4 22v-7',
}

function iconComponent(name) {
  const d = ICONS[name] || ICONS.file
  return {
    render() {
      return h('svg', {
        viewBox: '0 0 24 24',
        fill: 'none',
        stroke: 'currentColor',
        'stroke-width': '1.8',
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        class: 'w-4 h-4',
      }, d.split('M').filter(Boolean).map(seg =>
        h('path', { d: 'M' + seg })
      ))
    }
  }
}
</script>
