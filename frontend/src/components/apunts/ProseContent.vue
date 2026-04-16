<template>
  <div class="prose prose-sm dark:prose-invert max-w-none pt-2
              [&_code]:bg-gray-100 dark:[&_code]:bg-gray-800
              [&_pre]:overflow-x-auto [&_pre]:rounded-lg [&_pre]:p-3
              [&_.law-ref]:inline-block [&_.law-ref]:bg-blue-100 [&_.law-ref]:dark:bg-blue-900/30
              [&_.law-ref]:text-blue-700 [&_.law-ref]:dark:text-blue-300
              [&_.law-ref]:text-[0.7rem] [&_.law-ref]:font-semibold [&_.law-ref]:font-mono
              [&_.law-ref]:px-1.5 [&_.law-ref]:rounded"
       v-html="rendered" />
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps({
  content: { type: String, default: '' }
})

const LAW_REFS = ['LPACAP', 'LRJSP', 'LRBRL', 'LMRLC', 'LOPDGDD', 'LCSP', 'TRLCSP', 'EBEP', 'LOTAI', 'LOTC', 'CE']
const LAW_RE = new RegExp(`\\b(${LAW_REFS.join('|')})\\b`, 'g')

const rendered = computed(() => {
  const html = marked.parse(props.content || '', { breaks: true, gfm: true })
  const withBadges = html.replace(LAW_RE, '<span class="law-ref">$1</span>')
  return DOMPurify.sanitize(withBadges, { ADD_TAGS: ['span'], ADD_ATTR: ['class'] })
})
</script>
