<template>
  <div ref="wrapEl" class="relative" @mouseup="onSelectionEnd" @touchend="onSelectionEnd">
    <slot />
    <Transition name="fade">
      <div v-if="picker.visible"
           :style="{ top: picker.y + 'px', left: picker.x + 'px' }"
           class="fixed z-50 flex items-center gap-2 bg-white dark:bg-gray-800
                  border border-gray-200 dark:border-gray-700 shadow-lg
                  rounded-xl px-3 py-2">
        <button v-for="c in colors" :key="c.name"
                @click="applyAnnotation(c.name)"
                :class="c.bg"
                class="w-7 h-7 rounded-full border-2 border-white shadow hover:scale-110 transition-transform"
                :title="c.name" />
        <button @click="picker.visible = false"
                class="ml-1 text-gray-400 hover:text-gray-600 text-lg">✕</button>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { saveAnnotation } from '../../api/client.js'

const props = defineProps({ topicId: String })

const colors = [
  { name: 'yellow', bg: 'bg-yellow-300' },
  { name: 'blue',   bg: 'bg-blue-300'   },
  { name: 'green',  bg: 'bg-green-300'  },
]

const wrapEl = ref(null)
const picker = reactive({ visible: false, x: 0, y: 0 })
let lastSelection = null

function onSelectionEnd(e) {
  const sel = window.getSelection()
  if (!sel || sel.isCollapsed || !sel.toString().trim()) return
  lastSelection = sel.toString().trim()
  const range = sel.getRangeAt(0)
  const rect = range.getBoundingClientRect()
  picker.x = Math.min(rect.left, window.innerWidth - 180)
  picker.y = rect.bottom + 8
  picker.visible = true
}

async function applyAnnotation(color) {
  if (!lastSelection || !props.topicId) return
  picker.visible = false
  await saveAnnotation(props.topicId, {
    selected_text: lastSelection,
    color,
  })
  window.getSelection()?.removeAllRanges()
  lastSelection = null
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
