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

<style scoped>
.prose-content {
  font-size: 0.875rem;
  line-height: 1.75;
  color: var(--color-text, #1f2937);
}

/* Headings */
.prose-content :deep(h1),
.prose-content :deep(h2) {
  font-size: 1rem;
  font-weight: 800;
  color: #7c3aed;
  margin-top: 1.4em;
  margin-bottom: 0.4em;
  padding-bottom: 0.25em;
  border-bottom: 2px solid #ede9fe;
  letter-spacing: -0.01em;
}

.prose-content :deep(h3) {
  font-size: 0.875rem;
  font-weight: 700;
  color: #6d28d9;
  margin-top: 1.1em;
  margin-bottom: 0.3em;
}

.prose-content :deep(h4),
.prose-content :deep(h5),
.prose-content :deep(h6) {
  font-size: 0.8rem;
  font-weight: 700;
  color: #5b21b6;
  margin-top: 0.9em;
  margin-bottom: 0.2em;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* Paragraphs */
.prose-content :deep(p) {
  margin-top: 0;
  margin-bottom: 0.75em;
}

/* Bold */
.prose-content :deep(strong) {
  font-weight: 700;
  color: #111827;
}

/* Italic */
.prose-content :deep(em) {
  font-style: italic;
  color: #374151;
}

/* Lists */
.prose-content :deep(ul),
.prose-content :deep(ol) {
  margin: 0.5em 0 0.75em 0;
  padding-left: 1.4em;
}

.prose-content :deep(ul) {
  list-style-type: none;
  padding-left: 0;
}

.prose-content :deep(ul > li) {
  position: relative;
  padding-left: 1.25em;
  margin-bottom: 0.35em;
}

.prose-content :deep(ul > li::before) {
  content: '';
  position: absolute;
  left: 0;
  top: 0.6em;
  width: 6px;
  height: 6px;
  background: #7c3aed;
  border-radius: 50%;
}

.prose-content :deep(ol) {
  list-style-type: decimal;
}

.prose-content :deep(ol > li) {
  margin-bottom: 0.35em;
  padding-left: 0.25em;
}

.prose-content :deep(ol > li::marker) {
  color: #7c3aed;
  font-weight: 700;
}

/* Nested lists */
.prose-content :deep(li > ul) {
  margin-top: 0.25em;
  margin-bottom: 0.25em;
}

.prose-content :deep(li > ul > li::before) {
  width: 4px;
  height: 4px;
  background: #a78bfa;
}

/* Blockquote */
.prose-content :deep(blockquote) {
  border-left: 3px solid #7c3aed;
  padding: 0.5em 0.9em;
  margin: 0.75em 0;
  background: #faf5ff;
  border-radius: 0 8px 8px 0;
  color: #4b5563;
  font-style: normal;
}

/* Inline code */
.prose-content :deep(code) {
  background: #f3f4f6;
  color: #7c3aed;
  padding: 0.1em 0.35em;
  border-radius: 4px;
  font-size: 0.8em;
  font-family: ui-monospace, monospace;
}

/* Code block */
.prose-content :deep(pre) {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: 0.75em 1em;
  border-radius: 8px;
  overflow-x: auto;
  margin: 0.75em 0;
}

.prose-content :deep(pre code) {
  background: none;
  color: inherit;
  padding: 0;
  font-size: 0.8em;
}

/* Horizontal rule */
.prose-content :deep(hr) {
  border: none;
  border-top: 2px solid #ede9fe;
  margin: 1em 0;
}

/* Tables */
.prose-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
  margin: 0.75em 0;
}

.prose-content :deep(thead tr) {
  background: #f5f3ff;
}

.prose-content :deep(th) {
  text-align: left;
  font-weight: 700;
  color: #7c3aed;
  padding: 0.4em 0.6em;
  border-bottom: 2px solid #ede9fe;
}

.prose-content :deep(td) {
  padding: 0.35em 0.6em;
  border-bottom: 1px solid #f3f4f6;
}

.prose-content :deep(tr:last-child td) {
  border-bottom: none;
}

/* Law-ref badge */
.prose-content :deep(.law-ref) {
  display: inline-block;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 0.68rem;
  font-weight: 700;
  font-family: ui-monospace, monospace;
  padding: 0.1em 0.4em;
  border-radius: 4px;
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  .prose-content {
    color: #e5e7eb;
  }

  .prose-content :deep(h1),
  .prose-content :deep(h2) {
    color: #a78bfa;
    border-bottom-color: #3b1f6e;
  }

  .prose-content :deep(h3) {
    color: #c4b5fd;
  }

  .prose-content :deep(h4),
  .prose-content :deep(h5),
  .prose-content :deep(h6) {
    color: #ddd6fe;
  }

  .prose-content :deep(strong) {
    color: #f9fafb;
  }

  .prose-content :deep(em) {
    color: #d1d5db;
  }

  .prose-content :deep(ul > li::before) {
    background: #a78bfa;
  }

  .prose-content :deep(ol > li::marker) {
    color: #a78bfa;
  }

  .prose-content :deep(blockquote) {
    background: #1e1433;
    border-left-color: #a78bfa;
    color: #9ca3af;
  }

  .prose-content :deep(code) {
    background: #374151;
    color: #c4b5fd;
  }

  .prose-content :deep(thead tr) {
    background: #1e1433;
  }

  .prose-content :deep(th) {
    color: #a78bfa;
    border-bottom-color: #3b1f6e;
  }

  .prose-content :deep(td) {
    border-bottom-color: #374151;
  }

  .prose-content :deep(hr) {
    border-top-color: #3b1f6e;
  }

  .prose-content :deep(.law-ref) {
    background: #1e3a5f;
    color: #93c5fd;
  }
}
</style>
