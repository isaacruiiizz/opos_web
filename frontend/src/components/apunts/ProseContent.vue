<template>
  <div class="prose-content max-w-none pt-2" v-html="rendered" />
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

<!-- Not scoped: v-html children never receive scoped attributes.
     Dark mode targets .dark on <html> (class-based, set by ui store). -->
<style>
.prose-content {
  font-size: 0.875rem;
  line-height: 1.75;
  color: #1f2937;
}

/* Headings */
.prose-content h1,
.prose-content h2 {
  font-size: 1rem;
  font-weight: 800;
  color: #7c3aed;
  margin-top: 1.4em;
  margin-bottom: 0.4em;
  padding-bottom: 0.25em;
  border-bottom: 2px solid #ede9fe;
  letter-spacing: -0.01em;
}

.prose-content h3 {
  font-size: 0.875rem;
  font-weight: 700;
  color: #6d28d9;
  margin-top: 1.1em;
  margin-bottom: 0.3em;
}

.prose-content h4,
.prose-content h5,
.prose-content h6 {
  font-size: 0.8rem;
  font-weight: 700;
  color: #5b21b6;
  margin-top: 0.9em;
  margin-bottom: 0.2em;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.prose-content p {
  margin-top: 0;
  margin-bottom: 0.75em;
}

.prose-content strong {
  font-weight: 700;
  color: #111827;
}

.prose-content em {
  font-style: italic;
  color: #374151;
}

/* Lists */
.prose-content ul,
.prose-content ol {
  margin: 0.5em 0 0.75em 0;
  padding-left: 1.4em;
}

.prose-content ul {
  list-style-type: none;
  padding-left: 0;
}

.prose-content ul > li {
  position: relative;
  padding-left: 1.25em;
  margin-bottom: 0.35em;
}

.prose-content ul > li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0.6em;
  width: 6px;
  height: 6px;
  background: #7c3aed;
  border-radius: 50%;
}

.prose-content ol {
  list-style-type: decimal;
}

.prose-content ol > li {
  margin-bottom: 0.35em;
  padding-left: 0.25em;
}

.prose-content ol > li::marker {
  color: #7c3aed;
  font-weight: 700;
}

.prose-content li > ul {
  margin-top: 0.25em;
  margin-bottom: 0.25em;
}

.prose-content li > ul > li::before {
  width: 4px;
  height: 4px;
  background: #a78bfa;
}

/* Blockquote */
.prose-content blockquote {
  border-left: 3px solid #7c3aed;
  padding: 0.5em 0.9em;
  margin: 0.75em 0;
  background: #faf5ff;
  border-radius: 0 8px 8px 0;
  color: #4b5563;
  font-style: normal;
}

/* Code */
.prose-content code {
  background: #f3f4f6;
  color: #7c3aed;
  padding: 0.1em 0.35em;
  border-radius: 4px;
  font-size: 0.8em;
  font-family: ui-monospace, monospace;
}

.prose-content pre {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: 0.75em 1em;
  border-radius: 8px;
  overflow-x: auto;
  margin: 0.75em 0;
}

.prose-content pre code {
  background: none;
  color: inherit;
  padding: 0;
  font-size: 0.8em;
}

.prose-content hr {
  border: none;
  border-top: 2px solid #ede9fe;
  margin: 1em 0;
}

/* Tables */
.prose-content table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
  margin: 0.75em 0;
}

.prose-content thead tr {
  background: #f5f3ff;
}

.prose-content th {
  text-align: left;
  font-weight: 700;
  color: #7c3aed;
  padding: 0.4em 0.6em;
  border-bottom: 2px solid #ede9fe;
}

.prose-content td {
  padding: 0.35em 0.6em;
  border-bottom: 1px solid #f3f4f6;
}

.prose-content tr:last-child td {
  border-bottom: none;
}

/* Law-ref badge */
.prose-content .law-ref {
  display: inline-block;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 0.68rem;
  font-weight: 700;
  font-family: ui-monospace, monospace;
  padding: 0.1em 0.4em;
  border-radius: 4px;
}

/* ── Dark mode: keyed off .dark on <html>, not OS media query ── */
.dark .prose-content {
  color: #e5e7eb;
}

.dark .prose-content h1,
.dark .prose-content h2 {
  color: #a78bfa;
  border-bottom-color: #3b1f6e;
}

.dark .prose-content h3 {
  color: #c4b5fd;
}

.dark .prose-content h4,
.dark .prose-content h5,
.dark .prose-content h6 {
  color: #ddd6fe;
}

.dark .prose-content strong {
  color: #f9fafb;
}

.dark .prose-content em {
  color: #d1d5db;
}

.dark .prose-content ul > li::before {
  background: #a78bfa;
}

.dark .prose-content ol > li::marker {
  color: #a78bfa;
}

.dark .prose-content blockquote {
  background: #1e1433;
  border-left-color: #a78bfa;
  color: #9ca3af;
}

.dark .prose-content code {
  background: #374151;
  color: #c4b5fd;
}

.dark .prose-content pre {
  background: #12101e;
}

.dark .prose-content thead tr {
  background: #1e1433;
}

.dark .prose-content th {
  color: #a78bfa;
  border-bottom-color: #3b1f6e;
}

.dark .prose-content td {
  border-bottom-color: #374151;
}

.dark .prose-content hr {
  border-top-color: #3b1f6e;
}

.dark .prose-content .law-ref {
  background: #1e3a5f;
  color: #93c5fd;
}
</style>
