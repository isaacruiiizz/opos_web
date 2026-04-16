<template>
  <div class="px-4 pb-8">
    <SectionIndex :headings="headings" />
    <div ref="contentEl"
         class="prose prose-sm dark:prose-invert max-w-none
                [&_code]:bg-gray-100 dark:[&_code]:bg-gray-800
                [&_pre]:overflow-x-auto [&_pre]:rounded-lg [&_pre]:p-3"
         v-html="renderedHtml" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { marked, Renderer } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import SectionIndex from './SectionIndex.vue'

const props = defineProps({
  content: { type: String, default: '' },
  headings: { type: Array, default: () => [] }
})

const renderer = new Renderer()
renderer.heading = (token) => {
  const text = token.text
  const level = token.depth
  const anchor = text.toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
  return `<h${level} id="${anchor}" class="scroll-mt-16">${text}</h${level}>`
}

marked.use({
  renderer,
  breaks: true,
  gfm: true,
})

const renderedHtml = computed(() => marked.parse(props.content || ''))
</script>
