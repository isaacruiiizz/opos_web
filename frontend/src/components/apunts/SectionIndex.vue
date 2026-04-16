<template>
  <details class="mb-4 border border-[var(--color-border)] rounded-lg">
    <summary class="px-4 py-2 cursor-pointer font-semibold text-sm select-none">
      Índex del tema ▾
    </summary>
    <nav class="px-4 pb-3 space-y-0.5">
      <a v-for="h in headings" :key="h.anchor"
         :href="`#${h.anchor}`"
         :style="{ paddingLeft: `${(h.level - 2) * 12}px` }"
         class="block text-sm text-primary hover:underline py-0.5 truncate">
        {{ h.text }}
      </a>
    </nav>
  </details>
</template>

<script setup>
defineProps({ headings: { type: Array, default: () => [] } })
</script>
