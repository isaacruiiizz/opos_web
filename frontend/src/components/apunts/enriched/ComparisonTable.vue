<template>
  <div class="overflow-x-auto mt-1">
    <table class="w-full border-collapse text-xs">
      <thead>
        <tr class="bg-[#f5f3ff]">
          <th v-for="h in data.headers" :key="h"
              class="text-left text-primary font-bold px-2.5 py-1.5">{{ h }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, i) in data.rows" :key="i"
            class="border-b border-[var(--color-border)] last:border-0">
          <td v-for="(cell, j) in row" :key="j"
              class="px-2.5 py-1.5"
              :class="cellClass(i, j)">
            {{ cell }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
const props = defineProps({ data: { type: Object, required: true } })

function cellClass(rowIdx, colIdx) {
  if (colIdx === 0) return 'font-semibold'
  return ''
}
</script>
